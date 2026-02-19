"""Add PAUSED and CANCELLED to jobstatus enum.

Revision ID: 003
Revises: 002
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values; ignore if already present (e.g. re-run)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'jobstatus' AND e.enumlabel = 'PAUSED') THEN
                ALTER TYPE jobstatus ADD VALUE 'PAUSED';
            END IF;
        END$$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'jobstatus' AND e.enumlabel = 'CANCELLED') THEN
                ALTER TYPE jobstatus ADD VALUE 'CANCELLED';
            END IF;
        END$$;
    """)


def downgrade() -> None:
    # PostgreSQL does not support removing enum values easily; leave enum values in place.
    # Optionally: update any PAUSED/CANCELLED jobs to SCHEDULED/FAILED before downgrade.
    op.execute("UPDATE jobs SET status = 'SCHEDULED' WHERE status = 'PAUSED'")
    op.execute("UPDATE jobs SET status = 'FAILED' WHERE status = 'CANCELLED'")
    # We cannot DROP VALUE from enum in PG without recreating the type. Skip.
