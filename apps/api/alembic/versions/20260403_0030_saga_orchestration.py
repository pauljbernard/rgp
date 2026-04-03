"""add saga orchestration tables

Revision ID: 20260403_0030
Revises: 20260403_0029
Create Date: 2026-04-03 17:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260403_0030"
down_revision = "20260403_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saga_definitions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "saga_executions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("saga_definition_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("step_states", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("compensation_log", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("saga_executions")
    op.drop_table("saga_definitions")
