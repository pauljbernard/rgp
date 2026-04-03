"""runtime signal event ids

Revision ID: 20260331_0011
Revises: 20260331_0010
Create Date: 2026-03-31 17:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0011"
down_revision = "20260331_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("runtime_signals") as batch_op:
        batch_op.add_column(sa.Column("event_id", sa.String(length=128), nullable=True))
    op.execute("UPDATE runtime_signals SET event_id = 'legacy-' || id WHERE event_id IS NULL")
    with op.batch_alter_table("runtime_signals") as batch_op:
        batch_op.alter_column("event_id", nullable=False)
        batch_op.create_unique_constraint("uq_runtime_signals_event_id", ["event_id"])


def downgrade() -> None:
    with op.batch_alter_table("runtime_signals") as batch_op:
        batch_op.drop_constraint("uq_runtime_signals_event_id", type_="unique")
        batch_op.drop_column("event_id")
