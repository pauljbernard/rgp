"""add agent session governance fields

Revision ID: 20260403_0041
Revises: 20260403_0040
Create Date: 2026-04-03 23:55:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260403_0041"
down_revision = "20260403_0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = {column["name"] for column in inspector.get_columns("agent_sessions")}
    if "collaboration_mode" not in existing:
        op.add_column(
            "agent_sessions",
            sa.Column("collaboration_mode", sa.String(length=32), nullable=False, server_default="agent_assisted"),
        )
    if "agent_operating_profile" not in existing:
        op.add_column(
            "agent_sessions",
            sa.Column("agent_operating_profile", sa.String(length=64), nullable=False, server_default="general"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = {column["name"] for column in inspector.get_columns("agent_sessions")}
    if "agent_operating_profile" in existing:
        op.drop_column("agent_sessions", "agent_operating_profile")
    if "collaboration_mode" in existing:
        op.drop_column("agent_sessions", "collaboration_mode")
