"""add event outbox

Revision ID: 20260331_0016
Revises: 20260331_0015
Create Date: 2026-03-31 18:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0016"
down_revision = "20260331_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("event_store_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("partition_key", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("backend", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_event_outbox_status_id", "event_outbox", ["status", "id"])
    op.create_index("ix_event_outbox_event_store_id", "event_outbox", ["event_store_id"])


def downgrade() -> None:
    op.drop_index("ix_event_outbox_event_store_id", table_name="event_outbox")
    op.drop_index("ix_event_outbox_status_id", table_name="event_outbox")
    op.drop_table("event_outbox")
