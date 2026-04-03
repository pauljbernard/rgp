"""add policy engine tables

Revision ID: 20260403_0027
Revises: 20260403_0026
Create Date: 2026-04-03 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260403_0027"
down_revision = "20260403_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_rules",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("policy_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("condition", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("actions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "check_type_definitions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("handler_key", sa.String(255), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False, server_default="required"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("check_type_definitions")
    op.drop_table("policy_rules")
