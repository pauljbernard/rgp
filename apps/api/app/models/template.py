from datetime import datetime, timezone
from enum import StrEnum

from pydantic import Field

from app.models.common import RgpModel


class TemplateStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class TemplateRecord(RgpModel):
    id: str
    version: str
    name: str
    description: str
    status: TemplateStatus
    template_schema: dict = Field(default_factory=dict, alias="schema")
    created_at: datetime
    updated_at: datetime


class CreateTemplateVersionRequest(RgpModel):
    template_id: str
    version: str
    source_version: str | None = None
    name: str | None = None
    description: str | None = None


class UpdateTemplateDefinitionRequest(RgpModel):
    name: str
    description: str
    template_schema: dict = Field(default_factory=dict, alias="schema")


class TemplateStatusActionRequest(RgpModel):
    note: str | None = None


class TemplateValidationIssue(RgpModel):
    level: str
    path: str
    message: str


class TemplateValidationPreviewField(RgpModel):
    key: str
    title: str
    field_type: str
    required: bool
    default: str | int | float | bool | None = None
    enum_values: list[str] = Field(default_factory=list)
    description: str | None = None


class TemplateValidationPreview(RgpModel):
    field_count: int
    required_fields: list[str] = Field(default_factory=list)
    conditional_rule_count: int
    routing_rule_count: int = 0
    artifact_type_count: int = 0
    check_requirement_count: int = 0
    promotion_requirement_count: int = 0
    routed_fields: list[str] = Field(default_factory=list)
    fields: list[TemplateValidationPreviewField] = Field(default_factory=list)


class TemplateValidationResult(RgpModel):
    valid: bool
    issues: list[TemplateValidationIssue] = Field(default_factory=list)
    preview: TemplateValidationPreview


def seed_templates() -> list[TemplateRecord]:
    now = datetime.now(timezone.utc)
    return [
        TemplateRecord(
            id="tmpl_curriculum",
            version="3.1.0",
            name="Curriculum Generation",
            description="Generates a governed instructional unit.",
            status=TemplateStatus.PUBLISHED,
            schema={
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
                },
            },
            created_at=now,
            updated_at=now,
        )
    ]
