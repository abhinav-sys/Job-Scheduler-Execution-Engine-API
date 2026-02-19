"""Job API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app.models.job import Job, JobStatus, ScheduleType
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.services.job_service import JobService

router = APIRouter()


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
    status: JobStatus | None = Query(None, description="Filter by status"),
    schedule_type: ScheduleType | None = Query(None, description="Filter by schedule type"),
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
