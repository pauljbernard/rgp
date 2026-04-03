"""add advanced queue and assignment tables

Revision ID: 20260403_0039
Revises: 20260403_0038
Create Date: 2026-04-03 23:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260403_0039"
down_revision = "20260403_0038"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "assignment_groups",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("skill_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("max_capacity", sa.Integer(), nullable=True),
        sa.Column("current_load", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "escalation_rules",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("condition", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("escalation_target", sa.String(128), nullable=False),
        sa.Column("escalation_type", sa.String(32), nullable=False, server_default="reassign"),
        sa.Column("delay_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "sla_definitions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scope_type", sa.String(64), nullable=False),
        sa.Column("scope_id", sa.String(64), nullable=True),
        sa.Column("response_target_hours", sa.Float(), nullable=True),
        sa.Column("resolution_target_hours", sa.Float(), nullable=True),
        sa.Column("review_deadline_hours", sa.Float(), nullable=True),
        sa.Column("warning_threshold_pct", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "sla_breach_audit",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("sla_definition_id", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("breach_type", sa.String(64), nullable=False),
        sa.Column("target_hours", sa.Float(), nullable=False),
        sa.Column("actual_hours", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("remediation_action", sa.String(255), nullable=True),
        sa.Column("breached_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("sla_breach_audit")
    op.drop_table("sla_definitions")
    op.drop_table("escalation_rules")
    op.drop_table("assignment_groups")
