"""template routing refresh

Revision ID: 20260331_0014
Revises: 20260331_0013
Create Date: 2026-03-31 21:20:00.000000
"""

import json

import sqlalchemy as sa
from alembic import op


revision = "20260331_0014"
down_revision = "20260331_0013"
branch_labels = None
depends_on = None


CURRICULUM_SCHEMA = {
    "required": ["subject", "grade_level"],
    "routing": {
        "owner_team_by_field": {
            "subject": {
                "Math": "team_curriculum_math",
                "Science": "team_curriculum_science",
                "ELA": "team_curriculum_literacy",
                "History": "team_curriculum_social_studies",
            }
        },
        "workflow_binding_by_field": {
            "subject": {
                "Math": "wf_curriculum_math_v3",
                "Science": "wf_curriculum_science_v3",
                "ELA": "wf_curriculum_ela_v3",
                "History": "wf_curriculum_history_v3",
            }
        },
        "reviewers_by_field": {
            "subject": {
                "Math": ["reviewer_maya", "reviewer_olivia"],
                "Science": ["reviewer_nina", "reviewer_liam"],
                "ELA": ["reviewer_zoe", "reviewer_maya"],
                "History": ["reviewer_liam", "reviewer_isaac"],
            }
        },
        "promotion_approvers_by_field": {
            "subject": {
                "Math": ["ops_isaac"],
                "Science": ["ops_isaac"],
                "ELA": ["ops_maya"],
                "History": ["ops_maya"],
            }
        },
    },
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
}


ASSESSMENT_SCHEMA = {
    "required": ["assessment_id", "revision_reason"],
    "routing": {
        "owner_team": "team_assessment_quality",
        "workflow_binding": "wf_assessment_revision_v1",
        "reviewers": ["reviewer_liam", "reviewer_nina"],
        "promotion_approvers": ["ops_isaac"],
    },
    "properties": {
        "assessment_id": {"type": "string", "title": "Assessment ID"},
        "revision_reason": {
            "type": "string",
            "title": "Revision Reason",
            "enum": ["Standards alignment", "Difficulty adjustment", "Quality remediation"],
        },
        "target_window": {"type": "string", "title": "Target Window", "default": "Spring 2026"},
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_curriculum' AND version = '3.1.0'"),
        {"schema": json.dumps(CURRICULUM_SCHEMA)},
    )
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_assessment' AND version = '1.4.0'"),
        {"schema": json.dumps(ASSESSMENT_SCHEMA)},
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_curriculum' AND version = '3.1.0'"),
        {
            "schema": json.dumps(
                {
                    "required": ["subject", "grade_level"],
                    "properties": CURRICULUM_SCHEMA["properties"],
                }
            )
        },
    )
    bind.execute(
        sa.text("UPDATE templates SET schema = :schema WHERE id = 'tmpl_assessment' AND version = '1.4.0'"),
        {
            "schema": json.dumps(
                {
                    "required": ["assessment_id", "revision_reason"],
                    "properties": ASSESSMENT_SCHEMA["properties"],
                }
            )
        },
    )
