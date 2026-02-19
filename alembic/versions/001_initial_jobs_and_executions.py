"""Initial jobs and job_executions tables.

Revision ID: 001
Revises:
Create Date: 2025-02-19

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types only if they don't exist (e.g. API may have created them via create_all)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scheduletype') THEN
                CREATE TYPE scheduletype AS ENUM ('one_time', 'interval');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'jobstatus') THEN
                CREATE TYPE jobstatus AS ENUM ('SCHEDULED', 'RUNNING', 'COMPLETED', 'FAILED');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'executionstatus') THEN
                CREATE TYPE executionstatus AS ENUM ('SUCCESS', 'FAILED');
            END IF;
        END$$;
    """)
    # Create tables with raw SQL (one statement per op.execute for asyncpg; IF NOT EXISTS for idempotency)
    op.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id UUID NOT NULL PRIMARY KEY,
            name TEXT NOT NULL,
            payload JSONB,
            schedule_type scheduletype NOT NULL,
            run_at TIMESTAMP WITH TIME ZONE,
            interval_seconds INTEGER,
            max_retries INTEGER NOT NULL,
            status jobstatus NOT NULL,
            retry_count INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            version INTEGER NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_name ON jobs (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs (status)")
    op.execute("""
        CREATE TABLE IF NOT EXISTS job_executions (
            id UUID NOT NULL PRIMARY KEY,
            job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            attempt_number INTEGER NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            finished_at TIMESTAMP WITH TIME ZONE,
            status executionstatus NOT NULL,
            error_message TEXT
        )
    """)


def downgrade() -> None:
    op.drop_table("job_executions")
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_name"), table_name="jobs")
    op.drop_table("jobs")
    op.execute("DROP TYPE IF EXISTS executionstatus")
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS scheduletype")
