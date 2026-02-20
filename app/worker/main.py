"""Worker: poll DB, claim jobs with FOR UPDATE SKIP LOCKED, execute real work, handle retries and crash recovery."""
import asyncio
import os
import random
import sys
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Tuple

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import async_session_factory
from app.models.job import (
    Job,
    JobExecution,
    JobStatus,
    ScheduleType,
    ExecutionStatus,
)


POLL_INTERVAL = settings.WORKER_POLL_INTERVAL_SECONDS
STALE_MINUTES = settings.WORKER_STALE_RUNNING_MINUTES
SLEEP_MIN = settings.WORKER_EXECUTION_MIN_SLEEP
SLEEP_MAX = settings.WORKER_EXECUTION_MAX_SLEEP
FAILURE_PROBABILITY = settings.WORKER_FAILURE_PROBABILITY


async def reset_stale_running_jobs(session: AsyncSession) -> int:
    """Crash recovery: reset RUNNING jobs older than threshold to SCHEDULED."""
    threshold = datetime.now(timezone.utc) - timedelta(minutes=STALE_MINUTES)
    result = await session.execute(
        update(Job)
        .where(Job.status == JobStatus.RUNNING, Job.updated_at < threshold)
        .values(status=JobStatus.SCHEDULED)
    )
    return result.rowcount or 0


def _run_at_ready(job: Job) -> bool:
    if job.run_at is None:
        return True
    return job.run_at <= datetime.now(timezone.utc)


async def fetch_next_job(session: AsyncSession) -> Optional[Job]:
    """Select one SCHEDULED job ready to run, with FOR UPDATE SKIP LOCKED."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Job)
        .where(Job.status == JobStatus.SCHEDULED)
        .where((Job.run_at.is_(None)) | (Job.run_at <= now))
        .order_by(Job.run_at.asc().nulls_first())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    return job


def _is_webhook_url(url: str) -> bool:
    """True if this looks like a valid HTTP(S) URL for webhook."""
    u = (url or "").strip()
    return bool(u and isinstance(u, str) and (u.startswith("http://") or u.startswith("https://")))


async def _do_webhook(job: Job) -> Tuple[bool, str]:
    """POST job details to webhook_url in payload. Returns (success, message)."""
    payload = job.payload if isinstance(job.payload, dict) else {}
    url = (payload.get("webhook_url") or payload.get("callback_url") or "").strip()
    if not _is_webhook_url(url):
        return False, ""
    body = {
        "job_id": str(job.id),
        "job_name": job.name,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "schedule_type": job.schedule_type.value,
        "attempt": job.retry_count + 1,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            r = await client.post(url, json=body)
            if 200 <= r.status_code < 300:
                return True, f"Webhook delivered to {url[:50]}... (HTTP {r.status_code})"
            return False, f"Webhook returned HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


async def _do_fetch_quote() -> Tuple[bool, str]:
    """Fetch a random quote from a public API. Returns (success, quote or error)."""
    try:
        async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
            r = await client.get("https://api.quotable.io/random")
            if r.status_code != 200:
                return False, f"Quote API returned HTTP {r.status_code}"
            data = r.json()
            content = data.get("content", "").strip()
            author = data.get("author", "Unknown")
            return True, f'"{content}" — {author}'
    except Exception as e:
        return False, str(e)


async def execute_job(session: AsyncSession, job: Job) -> Tuple[bool, Optional[str]]:
    """
    Do real work: webhook POST if payload has webhook_url, else fetch a real quote from API.
    Returns (success, result_message or error_message).
    """
    await asyncio.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    if random.random() < FAILURE_PROBABILITY:
        return False, "Simulated failure (for retry testing)"

    success, message = await _do_webhook(job)
    if success:
        return True, message
    if message:
        return False, f"Webhook failed: {message}"

    success, result = await _do_fetch_quote()
    return success, result


async def process_one_job(session: AsyncSession) -> bool:
    """
    Fetch one job (FOR UPDATE SKIP LOCKED), run it, update status and executions.
    Returns True if a job was processed, False if none available.
    """
    job = await fetch_next_job(session)
    if job is None:
        return False

    attempt = job.retry_count + 1
    execution = JobExecution(
        job_id=job.id,
        attempt_number=attempt,
        status=ExecutionStatus.FAILED,
        error_message=None,
    )
    session.add(execution)
    job.status = JobStatus.RUNNING
    await session.flush()

    success, result_message = await execute_job(session, job)

    now = datetime.now(timezone.utc)
    execution.finished_at = now
    if success:
        execution.status = ExecutionStatus.SUCCESS
        execution.result = result_message
        if job.schedule_type == ScheduleType.INTERVAL and job.interval_seconds:
            job.status = JobStatus.SCHEDULED
            job.run_at = now + timedelta(seconds=job.interval_seconds)
        else:
            job.status = JobStatus.COMPLETED
    else:
        execution.error_message = result_message or "Execution failed"
        if attempt >= job.max_retries:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.SCHEDULED
            job.retry_count = attempt  # so next run is attempt+1

    await session.flush()
    return True


async def run_crash_recovery(session: AsyncSession) -> None:
    n = await reset_stale_running_jobs(session)
    if n:
        print(f"Crash recovery: reset {n} stale RUNNING job(s) to SCHEDULED", flush=True)
    await session.commit()


async def run_execute_pending_jobs(max_jobs: int = 10) -> Tuple[int, int]:
    """
    One-shot: run crash recovery then process up to max_jobs pending jobs.
    Used by POST /api/cron/execute-pending-jobs (GitHub Actions cron).
    Returns (stale_reset_count, jobs_processed_count).
    """
    stale_reset = 0
    async with async_session_factory() as session:
        try:
            stale_reset = await reset_stale_running_jobs(session)
            await session.commit()
            if stale_reset:
                print(f"Crash recovery: reset {stale_reset} stale RUNNING job(s) to SCHEDULED", flush=True)
        except Exception:
            await session.rollback()
            raise

    processed = 0
    for _ in range(max_jobs):
        async with async_session_factory() as session:
            try:
                did_one = await process_one_job(session)
                if did_one:
                    await session.commit()
                    processed += 1
                else:
                    break
            except Exception:
                await session.rollback()
                raise
    return stale_reset, processed


async def worker_loop() -> None:
    while True:
        async with async_session_factory() as session:
            try:
                await run_crash_recovery(session)
            except Exception as e:
                print(f"Crash recovery error: {e}", flush=True)
                await session.rollback()

        async with async_session_factory() as session:
            try:
                processed = await process_one_job(session)
                if processed:
                    await session.commit()
                # else no job claimed, nothing to commit
            except Exception as e:
                print(f"Process job error: {e}", flush=True)
                await session.rollback()

        await asyncio.sleep(POLL_INTERVAL)


def _run_health_server(port: int) -> None:
    """Run a minimal HTTP server for Fly.io / Render health checks (runs in a daemon thread)."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        def log_message(self, format: str, *args: object) -> None:
            pass
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

def main() -> None:
    # When running in same container as API (RUN_WORKER=true), use different port so API keeps PORT
    port = int(os.environ.get("WORKER_HEALTH_PORT", os.environ.get("PORT", "8080")))
    t = threading.Thread(target=_run_health_server, args=(port,), daemon=True)
    t.start()
    print("Worker started (poll every %s s, stale threshold %s min, health on :%s)" % (POLL_INTERVAL, STALE_MINUTES, port), flush=True)
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        print("Worker stopped", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
