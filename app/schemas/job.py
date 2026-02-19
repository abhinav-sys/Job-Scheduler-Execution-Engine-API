"""Pydantic schemas for Job and JobExecution."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.job import JobStatus, ScheduleType


class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    payload: dict[str, Any] | None = None
    schedule_type: ScheduleType
    run_at: datetime | None = None
    interval_seconds: int | None = None
    max_retries: int = Field(default=3, ge=0, le=100)

    @field_validator("run_at")
    @classmethod
    def run_at_must_be_future(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        if v.tzinfo is None:
            raise ValueError("run_at must be timezone-aware")
        from datetime import timezone
        if v <= datetime.now(timezone.utc):
            raise ValueError("run_at must be in the future")
        return v

    @field_validator("interval_seconds")
    @classmethod
    def interval_positive(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("interval_seconds must be greater than 0")
        return v

    def model_post_init(self, __context: Any) -> None:
        if self.schedule_type == ScheduleType.ONE_TIME and self.run_at is None:
            raise ValueError("one_time jobs require run_at")
        if self.schedule_type == ScheduleType.INTERVAL and self.interval_seconds is None:
            raise ValueError("interval jobs require interval_seconds")
        if self.schedule_type == ScheduleType.ONE_TIME and self.interval_seconds is not None:
            raise ValueError("one_time jobs must not have interval_seconds")


class JobExecutionResponse(BaseModel):
    id: UUID
    job_id: UUID
    attempt_number: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    error_message: str | None

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: UUID
    name: str
    payload: dict[str, Any] | None
    schedule_type: ScheduleType
    run_at: datetime | None
    interval_seconds: int | None
    max_retries: int
    status: JobStatus
    retry_count: int
    created_at: datetime
    updated_at: datetime
    version: int
    executions: list[JobExecutionResponse] = []

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
