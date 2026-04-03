"""add billing and quota tables

Revision ID: 20260403_0038
Revises: 20260403_0037
Create Date: 2026-04-03 22:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260403_0038"
down_revision = "20260403_0037"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "usage_meters",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("meter_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(32), nullable=False, server_default="count"),
        sa.Column("cost_amount", sa.Float(), nullable=True),
        sa.Column("cost_currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("attributed_to", sa.String(128), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "quota_definitions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("meter_type", sa.String(64), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(32), nullable=False, server_default="monthly"),
        sa.Column("enforcement", sa.String(32), nullable=False, server_default="soft"),
        sa.Column("budget_amount", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("quota_definitions")
    op.drop_table("usage_meters")
