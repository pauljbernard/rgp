"""add editorial workflow and content projection tables

Revision ID: 20260403_0034
Revises: 20260403_0033
Create Date: 2026-04-03 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260403_0034"
down_revision = "20260403_0033"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "editorial_workflows",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("artifact_id", sa.String(64), nullable=True),
        sa.Column("current_stage", sa.String(64), nullable=False, server_default="drafting"),
        sa.Column("stages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("role_assignments", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "content_projections",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("artifact_id", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(128), nullable=False),
        sa.Column("projection_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("projected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_ref", sa.String(255), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table("content_projections")
    op.drop_table("editorial_workflows")
