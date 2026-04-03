"""add planning construct tables

Revision ID: 20260403_0036
Revises: 20260403_0035
Create Date: 2026-04-03 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260403_0036"
down_revision = "20260403_0035"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "planning_constructs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_team_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capacity_budget", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "planning_memberships",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("planning_construct_id", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("planning_memberships")
    op.drop_table("planning_constructs")
