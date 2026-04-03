"""add transition gate policy table

Revision ID: 20260331_0005
Revises: 20260330_0004
Create Date: 2026-03-31 11:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0005"
down_revision = "20260330_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transition_gates",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("policy_id", sa.String(length=64), nullable=False),
        sa.Column("gate_scope", sa.String(length=32), nullable=False),
        sa.Column("transition_target", sa.String(length=64), nullable=False),
        sa.Column("required_check_name", sa.String(length=255), nullable=False),
        sa.Column("gate_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("transition_gates")
