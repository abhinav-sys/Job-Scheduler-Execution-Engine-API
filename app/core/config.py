"""Application configuration."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/job_scheduler"

    # Worker
    WORKER_POLL_INTERVAL_SECONDS: int = 5
    WORKER_STALE_RUNNING_MINUTES: int = 10  # Crash recovery: reset RUNNING older than this
    WORKER_EXECUTION_MIN_SLEEP: int = 1
    WORKER_EXECUTION_MAX_SLEEP: int = 3
    WORKER_FAILURE_PROBABILITY: float = 0.3  # 30% random failure for simulation

    # API
    API_TITLE: str = "Job Scheduler & Execution Engine"
    API_VERSION: str = "1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
