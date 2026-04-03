"""add data governance tables

Revision ID: 20260403_0037
Revises: 20260403_0036
Create Date: 2026-04-03 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260403_0037"
down_revision = "20260403_0036"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "data_classifications",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("classification_level", sa.String(32), nullable=False, server_default="internal"),
        sa.Column("residency_zone", sa.String(64), nullable=True),
        sa.Column("retention_policy_id", sa.String(64), nullable=True),
        sa.Column("classified_by", sa.String(128), nullable=False),
        sa.Column("classified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "retention_policies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("action_on_expiry", sa.String(32), nullable=False, server_default="archive"),
        sa.Column("applies_to", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "data_lineage_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column("transformation", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("data_lineage_records")
    op.drop_table("retention_policies")
    op.drop_table("data_classifications")
