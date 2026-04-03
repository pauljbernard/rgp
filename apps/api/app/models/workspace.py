"""Pydantic models for workspaces and change sets."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from app.models.common import RgpModel

class WorkspaceRecord(RgpModel):
    id: str
    tenant_id: str
    request_id: str
    name: str
    status: str = "created"  # created, active, merged, abandoned
    owner_id: str = ""
    source_ref: str | None = None
    target_ref: str | None = None
    protected_targets: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

class CreateWorkspaceRequest(RgpModel):
    request_id: str
    name: str
    owner_id: str
    source_ref: str | None = None
    target_ref: str | None = None
    protected_targets: list[str] = []

class ChangeSetRecord(RgpModel):
    id: str
    tenant_id: str
    request_id: str
    workspace_id: str | None = None
    artifact_id: str | None = None
    status: str = "draft"  # draft, submitted, approved, applied, rejected
    version: int = 1
    diff_metadata: dict[str, Any] | None = None
    lineage: dict[str, Any] | None = None
    applicable_type: str = "generic"
    description: str | None = None
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

class CreateChangeSetRequest(RgpModel):
    request_id: str
    workspace_id: str | None = None
    artifact_id: str | None = None
    applicable_type: str = "generic"
    description: str | None = None
    diff_metadata: dict[str, Any] | None = None
