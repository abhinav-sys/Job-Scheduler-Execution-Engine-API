"""Worker: poll DB, claim jobs with FOR UPDATE SKIP LOCKED, execute, handle retries and crash recovery."""
import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone

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


async def fetch_next_job(session: AsyncSession) -> Job | None:
    """Select one SCHEDULED job ready to run, with FOR UPDATE SKIP LOCKED."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Job)
        .where(Job.status == JobStatus.SCHEDULED)
        .where((Job.run_at.is_(None)) | (Job.run_at <= now))
        .order_by(Job.run_at.asc().nulls_last())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    return job


async def execute_job(session: AsyncSession, job: Job) -> bool:
    """
    Simulate execution: sleep 1-3s, 30% random failure.
    Returns True on success, False on failure.
    """
    await asyncio.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    return random.random() >= FAILURE_PROBABILITY


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

    success = await execute_job(session, job)

    now = datetime.now(timezone.utc)
    execution.finished_at = now
    if success:
        execution.status = ExecutionStatus.SUCCESS
        if job.schedule_type == ScheduleType.INTERVAL and job.interval_seconds:
            job.status = JobStatus.SCHEDULED
            job.run_at = now + timedelta(seconds=job.interval_seconds)
        else:
            job.status = JobStatus.COMPLETED
    else:
        execution.error_message = "Simulated failure (30% probability)"
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


def main() -> None:
    print("Worker started (poll every %s s, stale threshold %s min)" % (POLL_INTERVAL, STALE_MINUTES), flush=True)
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        print("Worker stopped", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
