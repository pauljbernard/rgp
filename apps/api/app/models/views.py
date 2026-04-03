"""Pydantic models for multi-view projections, event replay, and deployment environments."""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any
from app.models.common import RgpModel

class ViewType(StrEnum):
    QUEUE = "queue"
    BOARD = "board"
    TIMELINE = "timeline"
    GRAPH = "graph"
    ARTIFACT = "artifact"
    ROADMAP = "roadmap"

class DeploymentMode(StrEnum):
    SAAS = "saas"
    PRIVATE = "private"
    HYBRID = "hybrid"
    AIR_GAPPED = "air_gapped"

class ViewDefinitionRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    view_type: str
    config: dict[str, Any] = {}
    status: str = "active"
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

class EventReplayCheckpoint(RgpModel):
    id: str
    tenant_id: str
    replay_scope: str
    scope_id: str
    last_event_id: int
    status: str = "active"
    replayed_at: datetime | None = None

class DeploymentEnvironmentRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    mode: str = DeploymentMode.SAAS
    isolation_level: str = "shared"
    config: dict[str, Any] = {}
    status: str = "active"
    created_at: datetime | None = None

class CreateViewDefinitionRequest(RgpModel):
    name: str
    view_type: ViewType
    config: dict[str, Any] = {}
