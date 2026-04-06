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


class DomainPackDetail(RgpModel):
    pack: DomainPackRecord
    installations: list[DomainPackInstallation]


class DomainPackContributionDelta(RgpModel):
    category: str
    added: list[str] = []
    removed: list[str] = []


class DomainPackComparison(RgpModel):
    current_pack_id: str
    current_version: str
    baseline_pack_id: str | None = None
    baseline_version: str | None = None
    deltas: list[DomainPackContributionDelta] = []
    summary: str


class DomainPackLineageEntry(RgpModel):
    pack_id: str
    version: str
    status: str
    created_at: datetime | None = None
    activated_at: datetime | None = None
    contribution_count: int = 0

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
