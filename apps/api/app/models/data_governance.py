"""Pydantic models for data governance."""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from app.models.common import RgpModel

class ClassificationLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class DataClassificationRecord(RgpModel):
    id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    classification_level: str = ClassificationLevel.INTERNAL
    residency_zone: str | None = None
    retention_policy_id: str | None = None
    classified_by: str = ""
    classified_at: datetime | None = None

class RetentionPolicyRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    retention_days: int
    action_on_expiry: str = "archive"
    applies_to: list[str] = []
    status: str = "active"
    created_at: datetime | None = None

class DataLineageRecord(RgpModel):
    id: str
    tenant_id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    transformation: str | None = None
    created_at: datetime | None = None

class ClassifyEntityRequest(RgpModel):
    entity_type: str
    entity_id: str
    classification_level: ClassificationLevel
    residency_zone: str | None = None
    retention_policy_id: str | None = None
