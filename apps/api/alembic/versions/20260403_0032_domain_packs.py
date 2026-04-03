"""add domain pack tables

Revision ID: 20260403_0032
Revises: 20260403_0031
Create Date: 2026-04-03 19:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260403_0032"
down_revision = "20260403_0031"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "domain_packs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("contributed_templates", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("contributed_artifact_types", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("contributed_workflows", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("contributed_policies", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "domain_pack_installations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("pack_id", sa.String(64), nullable=False),
        sa.Column("installed_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="installed"),
        sa.Column("installed_by", sa.String(128), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("domain_pack_installations")
    op.drop_table("domain_packs")
