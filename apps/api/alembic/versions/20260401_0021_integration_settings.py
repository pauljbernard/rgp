"""add integration settings

Revision ID: 20260401_0021
Revises: 20260401_0020
Create Date: 2026-04-01 18:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260401_0021"
down_revision = "20260401_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("integrations", sa.Column("settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
    op.execute(
        """
        UPDATE integrations
        SET settings = jsonb_build_object(
          'provider',
          CASE
            WHEN id = 'int_agent_copilot' THEN 'microsoft'
            WHEN id = 'int_agent_codex' THEN 'openai'
            WHEN id = 'int_agent_claude' THEN 'anthropic'
            WHEN id = 'int_001' THEN 'microsoft'
            ELSE NULL
          END,
          'base_url',
          CASE
            WHEN id = 'int_agent_copilot' THEN 'https://graph.microsoft.com/beta/copilot'
            WHEN id = 'int_agent_codex' THEN 'https://api.openai.com/v1'
            WHEN id = 'int_agent_claude' THEN 'https://api.anthropic.com/v1'
            WHEN id = 'int_001' THEN 'http://localhost:8001/api/v1/runtime/mock'
            ELSE NULL
          END,
          'model',
          CASE
            WHEN id = 'int_agent_codex' THEN 'gpt-5.4'
            WHEN id = 'int_agent_claude' THEN 'claude-sonnet-4-5'
            ELSE NULL
          END
        )
        WHERE id IN ('int_001', 'int_agent_copilot', 'int_agent_codex', 'int_agent_claude')
        """
    )
    op.alter_column("integrations", "settings", server_default=None)


def downgrade() -> None:
    op.drop_column("integrations", "settings")
