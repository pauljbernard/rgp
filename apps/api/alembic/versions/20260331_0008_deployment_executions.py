"""deployment executions

Revision ID: 20260331_0008
Revises: 20260331_0007
Create Date: 2026-03-31 14:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0008"
down_revision = "20260331_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deployment_executions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("promotion_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("integration_id", sa.String(length=64), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("strategy", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("deployment_executions")
