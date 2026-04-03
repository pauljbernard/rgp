"""artifact history

Revision ID: 20260330_0003
Revises: 20260330_0002
Create Date: 2026-03-30 12:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260330_0003"
down_revision = "20260330_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artifact_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_version_id", sa.String(length=64), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "artifact_lineage_edges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("from_version_id", sa.String(length=64), nullable=True),
        sa.Column("to_version_id", sa.String(length=64), nullable=False),
        sa.Column("relation", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("artifact_lineage_edges")
    op.drop_table("artifact_events")
