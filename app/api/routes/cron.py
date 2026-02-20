"""Cron endpoint for GitHub Actions: trigger execution of pending jobs."""
from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.worker.main import run_execute_pending_jobs

router = APIRouter()


def _check_cron_secret(x_cron_secret: str | None = Header(None, alias="X-Cron-Secret")) -> None:
    if not settings.CRON_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Cron not configured: set CRON_SECRET in environment and in GitHub Actions secrets",
        )
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Cron-Secret")


@router.post("/execute-pending-jobs")
async def execute_pending_jobs(
    x_cron_secret: str | None = Header(None, alias="X-Cron-Secret"),
) -> dict:
    """
    Run one tick: crash recovery + process up to 10 pending jobs.
    Called by GitHub Actions on a schedule. Requires header: X-Cron-Secret: <CRON_SECRET>.
    """
    _check_cron_secret(x_cron_secret)
    stale_reset, jobs_processed = await run_execute_pending_jobs(max_jobs=10)
    return {
        "ok": True,
        "stale_reset": stale_reset,
        "jobs_processed": jobs_processed,
    }
