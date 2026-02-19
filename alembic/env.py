"""Alembic environment (sync for migrations)."""
import asyncio
from logging.config import fileConfig

from alembic import context  # type: ignore[reportMissingImports]
from sqlalchemy.engine import Connection  # type: ignore[reportMissingImports]
from sqlalchemy.ext.asyncio import create_async_engine  # type: ignore[reportMissingImports]

from app.core.config import get_database_url
from app.models.base import Base
from app.models.job import Job, JobExecution  # noqa: F401 - register models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Normalized URL (postgres:// → postgresql+asyncpg) for Render/Neon
config.set_main_option("sqlalchemy.url", get_database_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_async_engine(url, pool_pre_ping=True)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
