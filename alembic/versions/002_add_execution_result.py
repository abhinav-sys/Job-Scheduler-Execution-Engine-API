"""Add result column to job_executions for real work output.

Revision ID: 002
Revises: 001
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE job_executions ADD COLUMN IF NOT EXISTS result TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE job_executions DROP COLUMN IF EXISTS result")
