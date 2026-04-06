"""Pydantic models for federated governance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.common import RgpModel


class ProjectionMappingRecord(RgpModel):
    id: str
    tenant_id: str
    integration_id: str
    entity_type: str
    entity_id: str
    external_system: str
    external_ref: str | None = None
    external_state: dict | None = None
    projection_status: str = "pending"
    last_projected_at: datetime | None = None
    last_synced_at: datetime | None = None
    adapter_type: str | None = None
    adapter_capabilities: list[str] = []
    sync_source: str | None = None
    conflicts: list[dict] = []
    supported_resolution_actions: list[str] = []
    resolution_guidance: str | None = None


class ReconciliationLogRecord(RgpModel):
    id: str
    projection_id: str
    action: str  # "created", "updated", "conflict", "resolved"
    detail: str | None = None
    resolved_by: str | None = None
    created_at: datetime | None = None


class CreateProjectionRequest(RgpModel):
    entity_type: str
    entity_id: str


class ResolveProjectionRequest(RgpModel):
    action: str
    resolved_by: str | None = None


class UpdateProjectionExternalStateRequest(RgpModel):
    external_status: str | None = None
    external_title: str | None = None
    external_ref: str | None = None
