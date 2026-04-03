"""idempotency keys

Revision ID: 20260331_0012
Revises: 20260331_0011
Create Date: 2026-03-31 18:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0012"
down_revision = "20260331_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("scope", sa.String(length=255), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_idempotency_lookup", "idempotency_keys", ["tenant_id", "scope", "idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_idempotency_lookup", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
