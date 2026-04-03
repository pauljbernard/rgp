"""Pydantic models for governed context bundles."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.common import RgpModel


class ContextBundleContents(RgpModel):
    """Structured contents of a context bundle."""
    request_data: dict = {}
    template_semantics: dict = {}
    workflow_state: dict = {}
    policy_constraints: list[dict] = []
    knowledge_artifacts: list[dict] = []
    relationship_graph: list[dict] = []
    prior_decisions: list[dict] = []
    external_bindings: list[dict] = []
    available_tools: list[dict] = []


class ContextBundleRecord(RgpModel):
    id: str
    tenant_id: str
    request_id: str
    session_id: str | None = None
    version: int = 1
    bundle_type: str = "assignment"
    contents: dict = {}
    policy_scope: dict | None = None
    assembled_by: str = ""
    assembled_at: datetime | None = None
    provenance: list[dict] = []


class ContextAccessLogRecord(RgpModel):
    id: str
    bundle_id: str
    accessor_type: str
    accessor_id: str
    accessed_resource: str
    access_result: str  # "granted", "denied", "degraded"
    policy_basis: dict | None = None
    accessed_at: datetime | None = None
