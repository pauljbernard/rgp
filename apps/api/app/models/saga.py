"""Pydantic models for saga orchestration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from app.models.common import RgpModel


class SagaStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class SagaStepState(RgpModel):
    step_index: int
    request_id: str | None = None
    status: str = "pending"
    compensation_status: str | None = None
    error: str | None = None


class SagaDefinitionRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    steps: list[dict] = []
    status: str = "draft"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SagaExecutionRecord(RgpModel):
    id: str
    tenant_id: str
    saga_definition_id: str
    status: str = SagaStatus.PENDING
    step_states: list[dict] = []
    compensation_log: list[dict] = []
    created_at: datetime | None = None
    completed_at: datetime | None = None
