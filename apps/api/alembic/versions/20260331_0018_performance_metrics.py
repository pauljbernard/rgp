"""add performance metrics ledger

Revision ID: 20260331_0018
Revises: 20260331_0017
Create Date: 2026-03-31 19:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0018"
down_revision = "20260331_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("metric_type", sa.String(length=64), nullable=False),
        sa.Column("route", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("span_id", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_performance_metrics_tenant_occurred_at", "performance_metrics", ["tenant_id", "occurred_at"])
    op.create_index("ix_performance_metrics_route_method", "performance_metrics", ["route", "method"])


def downgrade() -> None:
    op.drop_index("ix_performance_metrics_route_method", table_name="performance_metrics")
    op.drop_index("ix_performance_metrics_tenant_occurred_at", table_name="performance_metrics")
    op.drop_table("performance_metrics")
