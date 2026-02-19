"""Application configuration."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import-untyped]


def _normalize_database_url(url: str) -> str:
    """Use asyncpg driver; accept postgres:// from Render/Neon etc."""
    u = (url or "").strip()
    if u.startswith("postgres://"):
        return "postgresql+asyncpg://" + u[11:]
    if u.startswith("postgresql://") and "+asyncpg" not in u:
        return u.replace("postgresql://", "postgresql+asyncpg://", 1)
    return u


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database (set in .env or by Render/Neon; postgres:// auto-converted to postgresql+asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://localhost/postgres"

    @property
    def database_url_normalized(self) -> str:
        return _normalize_database_url(self.DATABASE_URL)

    # Worker
    WORKER_POLL_INTERVAL_SECONDS: int = 5
    WORKER_STALE_RUNNING_MINUTES: int = 10  # Crash recovery: reset RUNNING older than this
    WORKER_EXECUTION_MIN_SLEEP: int = 1
    WORKER_EXECUTION_MAX_SLEEP: int = 3
    WORKER_FAILURE_PROBABILITY: float = 0.0  # 0 = reliable demo; set 0.3 to test retries

    # API
    API_TITLE: str = "Job Scheduler & Execution Engine"
    API_VERSION: str = "1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# Use normalized URL everywhere (asyncpg)
def get_database_url() -> str:
    return settings.database_url_normalized
