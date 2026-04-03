from datetime import datetime, timezone
from enum import StrEnum

from pydantic import Field

from app.models.common import RgpModel


class RequestStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VALIDATION_FAILED = "validation_failed"
    VALIDATED = "validated"
    CLASSIFIED = "classified"
    OWNERSHIP_RESOLVED = "ownership_resolved"
    PLANNED = "planned"
    QUEUED = "queued"
    IN_EXECUTION = "in_execution"
    AWAITING_INPUT = "awaiting_input"
    AWAITING_REVIEW = "awaiting_review"
    UNDER_REVIEW = "under_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROMOTION_PENDING = "promotion_pending"
    PROMOTED = "promoted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    ARCHIVED = "archived"


class RequestPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RequestRecord(RgpModel):
    id: str
    tenant_id: str
    request_type: str
    template_id: str
    template_version: str
    title: str
    summary: str
    status: RequestStatus
    priority: RequestPriority
    sla_policy_id: str | None = None
    submitter_id: str
    owner_team_id: str | None = None
    owner_user_id: str | None = None
    workflow_binding_id: str | None = None
    current_run_id: str | None = None
    policy_context: dict = Field(default_factory=dict)
    input_payload: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int
    is_archived: bool = False
    sla_risk_level: str | None = None
    sla_risk_reason: str | None = None


class CreateRequestDraft(RgpModel):
    template_id: str
    template_version: str
    title: str
    summary: str
    priority: RequestPriority
    input_payload: dict = Field(default_factory=dict)


class SubmitRequest(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Submitted for governed processing"


class AmendRequest(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Request amended"
    title: str | None = None
    summary: str | None = None
    priority: RequestPriority | None = None
    input_payload: dict | None = None


class CancelRequest(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Request canceled"


class CloneRequest(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Request cloned"
    title: str | None = None
    summary: str | None = None


class SupersedeRequest(RgpModel):
    actor_id: str = "user_demo"
    replacement_request_id: str
    reason: str = "Superseded by successor request"


class TransitionRequest(RgpModel):
    actor_id: str = "user_demo"
    target_status: RequestStatus
    reason: str = "Status transitioned"


class RequestCheckRun(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Automated request checks executed"


def seed_request(
    request_id: str,
    title: str,
    status: RequestStatus,
    priority: RequestPriority,
    owner_team_id: str | None,
) -> RequestRecord:
    now = datetime.now(timezone.utc)
    return RequestRecord(
        id=request_id,
        tenant_id="tenant_demo",
        request_type="curriculum_generation",
        template_id="tmpl_curriculum",
        template_version="3.1.0",
        title=title,
        summary="Initial governed request scaffold",
        status=status,
        priority=priority,
        submitter_id="user_demo",
        owner_team_id=owner_team_id,
        created_at=now,
        created_by="seed",
        updated_at=now,
        updated_by="seed",
        version=1,
    )
