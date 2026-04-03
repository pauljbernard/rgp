"""add collaboration mode tracking

Revision ID: 20260403_0028
Revises: 20260403_0027
Create Date: 2026-04-03 16:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260403_0028"
down_revision = "20260403_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("requests", sa.Column("collaboration_mode", sa.String(32), nullable=True, server_default="human_led"))
    op.add_column("agent_sessions", sa.Column("collaboration_mode", sa.String(32), nullable=True, server_default="human_led"))

    op.create_table(
        "collaboration_mode_transitions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("from_mode", sa.String(32), nullable=False),
        sa.Column("to_mode", sa.String(32), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("policy_basis", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("collaboration_mode_transitions")
    op.drop_column("agent_sessions", "collaboration_mode")
    op.drop_column("requests", "collaboration_mode")
