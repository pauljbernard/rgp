"""request relationships

Revision ID: 20260330_0002
Revises: 20260330_0001
Create Date: 2026-03-30 11:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260330_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "request_relationships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_request_id", sa.String(length=64), nullable=False),
        sa.Column("target_request_id", sa.String(length=64), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("request_relationships")
