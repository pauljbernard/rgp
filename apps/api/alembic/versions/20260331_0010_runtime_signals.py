"""runtime signals

Revision ID: 20260331_0010
Revises: 20260331_0009
Create Date: 2026-03-31 15:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0010"
down_revision = "20260331_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_signals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_step", sa.String(length=255), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("runtime_signals")
