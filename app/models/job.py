"""Job and JobExecution models."""
import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, TypeDecorator, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ScheduleType(str, enum.Enum):
    ONE_TIME = "one_time"
    INTERVAL = "interval"


class ScheduleTypeColumn(TypeDecorator[str]):
    """Forces ScheduleType to be stored as its .value ('one_time'/'interval') in PostgreSQL."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(
                Enum(ScheduleType, name="scheduletype", create_type=False, values_callable=lambda x: [e.value for e in x])
            )
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, ScheduleType):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, ScheduleType):
            return value
        return ScheduleType(value) if value else None


class JobStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    schedule_type: Mapped[ScheduleType] = mapped_column(
        ScheduleTypeColumn(),
        nullable=False,
    )
    run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=JobStatus.SCHEDULED, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    executions: Mapped[list["JobExecution"]] = relationship(
        "JobExecution", back_populates="job", cascade="all, delete-orphan"
    )


class JobExecution(Base):
    __tablename__ = "job_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    job: Mapped["Job"] = relationship("Job", back_populates="executions")
