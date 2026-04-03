"""add tenants

Revision ID: 20260403_0025
Revises: 20260403_0024
Create Date: 2026-04-03 01:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260403_0025"
down_revision = "20260403_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    bind = op.get_bind()
    for tenant_id, name in [
        ("tenant_demo", "Demo Tenant"),
        ("tenant_other", "Other Tenant"),
    ]:
        bind.execute(
            sa.text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                "VALUES (:id, :name, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"id": tenant_id, "name": name},
        )


def downgrade() -> None:
    op.drop_table("tenants")
