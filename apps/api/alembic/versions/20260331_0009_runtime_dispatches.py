"""runtime dispatches

Revision ID: 20260331_0009
Revises: 20260331_0008
Create Date: 2026-03-31 14:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0009"
down_revision = "20260331_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_dispatches",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("integration_id", sa.String(length=64), nullable=False),
        sa.Column("dispatch_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("runtime_dispatches")
