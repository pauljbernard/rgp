"""add federation projection and reconciliation tables

Revision ID: 20260403_0031
Revises: 20260403_0030
Create Date: 2026-04-03 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260403_0031"
down_revision = "20260403_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projection_mappings",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("integration_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("external_system", sa.String(128), nullable=False),
        sa.Column("external_ref", sa.String(255), nullable=True),
        sa.Column("external_state", sa.JSON(), nullable=True),
        sa.Column("projection_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("last_projected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "reconciliation_log",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("projection_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reconciliation_log")
    op.drop_table("projection_mappings")
