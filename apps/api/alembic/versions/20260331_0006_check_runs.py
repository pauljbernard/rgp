"""add check run queue table

Revision ID: 20260331_0006
Revises: 20260331_0005
Create Date: 2026-03-31 12:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0006"
down_revision = "20260331_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "check_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("promotion_id", sa.String(length=64), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trigger_reason", sa.Text(), nullable=False),
        sa.Column("enqueued_by", sa.String(length=128), nullable=False),
        sa.Column("worker_task_id", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("check_runs")
