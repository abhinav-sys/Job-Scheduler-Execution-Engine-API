"""Job API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.job import Job, JobStatus, ScheduleType
from app.schemas.job import JobCreate, JobListResponse, JobResponse, JobUpdate
from app.services.job_service import JobService

router = APIRouter()

ALLOWED_STATUS_TRANSITIONS = {
    JobStatus.PAUSED: (JobStatus.SCHEDULED,),      # can only go to PAUSED from SCHEDULED
    JobStatus.SCHEDULED: (JobStatus.PAUSED,),     # resume: PAUSED -> SCHEDULED
    JobStatus.CANCELLED: (JobStatus.SCHEDULED, JobStatus.PAUSED, JobStatus.RUNNING),
}


@router.post("", response_model=JobResponse)
async def create_job(
    data: JobCreate,
    session: AsyncSession = Depends(get_async_session),
) -> Job:
    service = JobService(session)
    job = await service.create(data)
    await session.refresh(job, ["executions"])
    return job


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    schedule_type: Optional[ScheduleType] = Query(None, description="Filter by schedule type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> JobListResponse:
    service = JobService(session)
    jobs, total = await service.list_jobs(
        status=status,
        schedule_type=schedule_type,
        limit=limit,
        offset=offset,
    )
    for j in jobs:
        await session.refresh(j, ["executions"])
    return JobListResponse(jobs=jobs, total=total)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> Job:
    service = JobService(session)
    job = await service.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    await session.refresh(job, ["executions"])
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    data: JobUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> Job:
    if data.status is None:
        raise HTTPException(status_code=400, detail="status is required")
    allowed_from = ALLOWED_STATUS_TRANSITIONS.get(data.status)
    if not allowed_from:
        raise HTTPException(
            status_code=400,
            detail="Cannot set status to {} from API".format(data.status.value),
        )
    service = JobService(session)
    job = await service.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in allowed_from:
        raise HTTPException(
            status_code=400,
            detail="Cannot set status to {} when job is {}".format(
                data.status.value, job.status.value
            ),
        )
    job = await service.update_status(job_id, data.status)
    await session.refresh(job, ["executions"])
    return job


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    service = JobService(session)
    deleted = await service.delete(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
