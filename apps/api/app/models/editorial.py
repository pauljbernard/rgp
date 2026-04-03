"""Pydantic models for editorial workflows and content projection."""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any
from app.models.common import RgpModel

class EditorialRole(StrEnum):
    AUTHOR = "author"
    EDITOR = "editor"
    FACT_REVIEWER = "fact_reviewer"
    LEGAL_REVIEWER = "legal_reviewer"
    COMPLIANCE_REVIEWER = "compliance_reviewer"
    PUBLISHER = "publisher"

class EditorialStage(RgpModel):
    name: str
    required_role: str
    status: str = "pending"  # pending, in_progress, completed, skipped

class EditorialWorkflowRecord(RgpModel):
    id: str
    tenant_id: str
    request_id: str
    artifact_id: str | None = None
    current_stage: str = "drafting"
    stages: list[dict] = []
    role_assignments: dict[str, str] = {}
    created_at: datetime | None = None
    updated_at: datetime | None = None

class ContentProjectionRecord(RgpModel):
    id: str
    tenant_id: str
    artifact_id: str
    channel: str
    projection_status: str = "pending"
    projected_at: datetime | None = None
    external_ref: str | None = None
    config: dict[str, Any] | None = None

class CreateEditorialWorkflowRequest(RgpModel):
    request_id: str
    artifact_id: str | None = None
    stages: list[dict] = []
    role_assignments: dict[str, str] = {}
