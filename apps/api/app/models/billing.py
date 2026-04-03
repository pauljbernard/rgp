"""Pydantic models for billing and quotas."""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from app.models.common import RgpModel

class MeterType(StrEnum):
    REQUEST_CREATED = "request_created"
    RUN_EXECUTED = "run_executed"
    ARTIFACT_STORED = "artifact_stored"
    REVIEW_COMPLETED = "review_completed"
    PROMOTION_EXECUTED = "promotion_executed"
    AGENT_INVOCATION = "agent_invocation"
    API_CALL = "api_call"
    STORAGE_BYTES = "storage_bytes"

class QuotaEnforcement(StrEnum):
    SOFT = "soft"
    HARD = "hard"

class UsageMeterRecord(RgpModel):
    id: str
    tenant_id: str
    meter_type: str
    resource_id: str | None = None
    quantity: int = 1
    unit: str = "count"
    cost_amount: float | None = None
    cost_currency: str = "USD"
    attributed_to: str | None = None
    recorded_at: datetime | None = None

class QuotaDefinitionRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    meter_type: str
    limit_value: int
    period: str = "monthly"
    enforcement: str = QuotaEnforcement.SOFT
    budget_amount: float | None = None
    status: str = "active"
    created_at: datetime | None = None

class RecordUsageRequest(RgpModel):
    meter_type: MeterType
    resource_id: str | None = None
    quantity: int = 1
    cost_amount: float | None = None
    attributed_to: str | None = None

class CreateQuotaRequest(RgpModel):
    name: str
    meter_type: MeterType
    limit_value: int
    period: str = "monthly"
    enforcement: QuotaEnforcement = QuotaEnforcement.SOFT
    budget_amount: float | None = None
