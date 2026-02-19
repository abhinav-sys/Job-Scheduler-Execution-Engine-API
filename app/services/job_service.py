"""Job CRUD and business logic."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus, ScheduleType
from app.schemas.job import JobCreate


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: JobCreate) -> Job:
        job = Job(
            name=data.name,
            payload=data.payload,
            schedule_type=data.schedule_type,
            run_at=data.run_at,
            interval_seconds=data.interval_seconds,
            max_retries=data.max_retries,
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: UUID) -> Job | None:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        schedule_type: ScheduleType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        q = select(Job)
        count_q = select(func.count()).select_from(Job)
        if status is not None:
            q = q.where(Job.status == status)
            count_q = count_q.where(Job.status == status)
        if schedule_type is not None:
            q = q.where(Job.schedule_type == schedule_type)
            count_q = count_q.where(Job.schedule_type == schedule_type)
        total_count = (await self.session.execute(count_q)).scalar_one()
        q = q.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        jobs = list(result.scalars().all())
        return jobs, total_count
