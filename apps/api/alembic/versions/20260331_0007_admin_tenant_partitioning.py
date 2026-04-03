"""admin tenant partitioning

Revision ID: 20260331_0007
Revises: 20260331_0006
Create Date: 2026-03-31 13:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0007"
down_revision = "20260331_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("templates") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="tenant_demo"))
    with op.batch_alter_table("capabilities") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="tenant_demo"))
    with op.batch_alter_table("policies") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="tenant_demo"))
    with op.batch_alter_table("transition_gates") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="tenant_demo"))
    with op.batch_alter_table("integrations") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="tenant_demo"))


def downgrade() -> None:
    with op.batch_alter_table("integrations") as batch_op:
        batch_op.drop_column("tenant_id")
    with op.batch_alter_table("transition_gates") as batch_op:
        batch_op.drop_column("tenant_id")
    with op.batch_alter_table("policies") as batch_op:
        batch_op.drop_column("tenant_id")
    with op.batch_alter_table("capabilities") as batch_op:
        batch_op.drop_column("tenant_id")
    with op.batch_alter_table("templates") as batch_op:
        batch_op.drop_column("tenant_id")
