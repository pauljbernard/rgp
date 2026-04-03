"""Pydantic models for domain packs."""
from __future__ import annotations
from datetime import datetime
from app.models.common import RgpModel

class DomainPackRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    version: str
    description: str | None = None
    status: str = "draft"
    contributed_templates: list[str] = []
    contributed_artifact_types: list[str] = []
    contributed_workflows: list[str] = []
    contributed_policies: list[str] = []
    activated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

class DomainPackInstallation(RgpModel):
    id: str
    tenant_id: str
    pack_id: str
    installed_version: str
    status: str = "installed"
    installed_by: str = ""
    installed_at: datetime | None = None

class CreateDomainPackRequest(RgpModel):
    name: str
    version: str
    description: str | None = None
    contributed_templates: list[str] = []
    contributed_artifact_types: list[str] = []
    contributed_workflows: list[str] = []
    contributed_policies: list[str] = []

class ActivateDomainPackRequest(RgpModel):
    actor_id: str
    reason: str = ""
