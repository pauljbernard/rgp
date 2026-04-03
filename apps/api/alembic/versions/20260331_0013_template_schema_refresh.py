"""template schema refresh

Revision ID: 20260331_0013
Revises: 20260331_0012
Create Date: 2026-03-31 19:00:00.000000
"""

from alembic import op
import json
import sqlalchemy as sa


revision = "20260331_0013"
down_revision = "20260331_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_curriculum' AND version = '3.1.0'"),
        {
            "schema": json.dumps({
                "required": ["subject", "grade_level"],
                "properties": {
                    "subject": {
                        "type": "string",
                        "title": "Subject",
                        "enum": ["Math", "Science", "ELA", "History"],
                        "default": "Math",
                    },
                    "grade_level": {
                        "type": "string",
                        "title": "Grade Level",
                        "enum": ["Grade 3", "Grade 4", "Grade 5", "Grade 6"],
                    },
                    "locale": {
                        "type": "string",
                        "title": "Locale",
                        "enum": ["en-US", "en-GB", "es-US"],
                        "default": "en-US",
                    },
                },
            })
        },
    )
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_assessment' AND version = '1.4.0'"),
        {
            "schema": json.dumps({
                "required": ["assessment_id", "revision_reason"],
                "properties": {
                    "assessment_id": {"type": "string", "title": "Assessment ID"},
                    "revision_reason": {
                        "type": "string",
                        "title": "Revision Reason",
                        "enum": ["Standards alignment", "Difficulty adjustment", "Quality remediation"],
                    },
                    "target_window": {"type": "string", "title": "Target Window", "default": "Spring 2026"},
                },
            })
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_curriculum' AND version = '3.1.0'"),
        {
            "schema": json.dumps({
                "required": ["subject", "grade_level"],
                "properties": {
                    "subject": {"type": "string"},
                    "grade_level": {"type": "string"},
                },
            })
        },
    )
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_assessment' AND version = '1.4.0'"),
        {
            "schema": json.dumps({"required": ["assessment_id", "revision_reason"]})
        },
    )
