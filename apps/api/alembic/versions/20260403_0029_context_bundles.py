"""add context bundle and access log tables

Revision ID: 20260403_0029
Revises: 20260403_0028
Create Date: 2026-04-03 17:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260403_0029"
down_revision = "20260403_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "context_bundles",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bundle_type", sa.String(32), nullable=False, server_default="assignment"),
        sa.Column("contents", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("policy_scope", sa.JSON(), nullable=True),
        sa.Column("assembled_by", sa.String(128), nullable=False),
        sa.Column("assembled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "context_access_log",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("bundle_id", sa.String(64), nullable=False),
        sa.Column("accessor_type", sa.String(32), nullable=False),
        sa.Column("accessor_id", sa.String(64), nullable=False),
        sa.Column("accessed_resource", sa.String(255), nullable=False),
        sa.Column("access_result", sa.String(32), nullable=False),
        sa.Column("policy_basis", sa.JSON(), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("context_access_log")
    op.drop_table("context_bundles")
