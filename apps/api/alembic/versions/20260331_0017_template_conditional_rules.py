"""refresh template schemas with conditional validation rules

Revision ID: 20260331_0017
Revises: 20260331_0016
Create Date: 2026-03-31 23:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_0017"
down_revision = "20260331_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    templates = sa.table(
        "templates",
        sa.column("id", sa.String()),
        sa.column("schema", sa.JSON()),
    )
    connection.execute(
        templates.update()
        .where(templates.c.id == "tmpl_curriculum")
        .values(
            {
                "schema": {
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
                        "subject": {"type": "string", "title": "Subject", "enum": ["Math", "Science", "ELA", "History"], "default": "Math"},
                        "grade_level": {"type": "string", "title": "Grade Level", "enum": ["Grade 3", "Grade 4", "Grade 5", "Grade 6"]},
                        "locale": {"type": "string", "title": "Locale", "enum": ["en-US", "en-GB", "es-US"], "default": "en-US"},
                        "delivery_model": {"type": "string", "title": "Delivery Model", "enum": ["Core", "Intervention", "Enrichment"], "default": "Core"},
                        "lab_materials": {
                            "type": "string",
                            "title": "Lab Materials",
                            "description": "Required for science requests. Include enough detail for the governed lab plan.",
                            "min_length": 10,
                        },
                        "reading_focus": {
                            "type": "string",
                            "title": "Reading Focus",
                            "description": "Required for ELA requests to determine the correct review package.",
                            "enum": ["Literary analysis", "Informational text", "Foundational skills"],
                        },
                    },
                    "conditional_required": [
                        {
                            "when": {"field": "subject", "equals": "Science"},
                            "field": "lab_materials",
                            "message": "Template validation failed for lab_materials: Science requests require lab materials.",
                        },
                        {
                            "when": {"field": "subject", "equals": "ELA"},
                            "field": "reading_focus",
                            "message": "Template validation failed for reading_focus: ELA requests require a reading focus.",
                        },
                    ],
                }
            }
        )
    )
    connection.execute(
        templates.update()
        .where(templates.c.id == "tmpl_assessment")
        .values(
            {
                "schema": {
                    "required": ["assessment_id", "revision_reason"],
                    "routing": {
                        "owner_team": "team_assessment_quality",
                        "workflow_binding": "wf_assessment_revision_v1",
                        "reviewers": ["reviewer_liam", "reviewer_nina"],
                        "promotion_approvers": ["ops_isaac"],
                    },
                    "properties": {
                        "assessment_id": {"type": "string", "title": "Assessment ID", "pattern": r"asm_[A-Za-z0-9_-]+$"},
                        "revision_reason": {
                            "type": "string",
                            "title": "Revision Reason",
                            "enum": ["Standards alignment", "Difficulty adjustment", "Quality remediation"],
                        },
                        "target_window": {"type": "string", "title": "Target Window", "default": "Spring 2026", "min_length": 6},
                    },
                }
            }
        )
    )


def downgrade() -> None:
    pass
