"""Pydantic models for knowledge artifacts."""
from __future__ import annotations
from datetime import datetime
from app.models.common import RgpModel

class KnowledgeArtifactRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    description: str | None = None
    content: str | None = None
    content_type: str = "text"
    version: int = 1
    status: str = "draft"  # draft, published, deprecated, archived
    policy_scope: dict | None = None
    provenance: list[dict] = []
    tags: list[str] = []
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

class KnowledgeVersionRecord(RgpModel):
    id: str
    artifact_id: str
    version: int
    content: str | None = None
    summary: str | None = None
    author: str = ""
    created_at: datetime | None = None

class CreateKnowledgeArtifactRequest(RgpModel):
    name: str
    description: str | None = None
    content: str | None = None
    content_type: str = "text"
    tags: list[str] = []
    policy_scope: dict | None = None
