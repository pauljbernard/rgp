"""add user account lifecycle fields

Revision ID: 20260402_0023
Revises: 20260401_0022
Create Date: 2026-04-02 23:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0023"
down_revision = "20260401_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("password_reset_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("registration_request_id", sa.String(length=64), nullable=True))
    op.alter_column("users", "password_reset_required", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "registration_request_id")
    op.drop_column("users", "password_reset_required")
    op.drop_column("users", "password_hash")
