"""add unified event store

Revision ID: 20260331_0015
Revises: 20260331_0014
Create Date: 2026-03-31 18:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0015"
down_revision = "20260331_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_store",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("run_id", sa.String(length=64), nullable=True),
        sa.Column("artifact_id", sa.String(length=64), nullable=True),
        sa.Column("promotion_id", sa.String(length=64), nullable=True),
        sa.Column("check_run_id", sa.String(length=64), nullable=True),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_event_store_tenant_occurred_at", "event_store", ["tenant_id", "occurred_at"])
    op.create_index("ix_event_store_request_id", "event_store", ["request_id"])
    op.create_index("ix_event_store_run_id", "event_store", ["run_id"])
    op.create_index("ix_event_store_artifact_id", "event_store", ["artifact_id"])
    op.create_index("ix_event_store_promotion_id", "event_store", ["promotion_id"])


def downgrade() -> None:
    op.drop_index("ix_event_store_promotion_id", table_name="event_store")
    op.drop_index("ix_event_store_artifact_id", table_name="event_store")
    op.drop_index("ix_event_store_run_id", table_name="event_store")
    op.drop_index("ix_event_store_request_id", table_name="event_store")
    op.drop_index("ix_event_store_tenant_occurred_at", table_name="event_store")
    op.drop_table("event_store")
