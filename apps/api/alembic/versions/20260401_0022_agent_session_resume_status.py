"""add resume request status to agent sessions

Revision ID: 20260401_0022
Revises: 20260401_0021
Create Date: 2026-04-01 20:50:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260401_0022"
down_revision = "20260401_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_sessions", sa.Column("resume_request_status", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_sessions", "resume_request_status")
