"""Canonical Pydantic models for substrate-neutral communication.

These models define the contract between RGP governance and external
execution/deployment substrates.  They are substrate-agnostic — adapters
translate them into substrate-specific representations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Runtime dispatch
# ---------------------------------------------------------------------------

class CanonicalRunDispatch(BaseModel):
    """Payload sent to a runtime adapter to start or continue a run."""

    request_id: str
    run_id: str
    dispatch_type: str = "workflow"
    workflow_binding_id: str | None = None
    template_id: str | None = None
    template_version: str | None = None
    priority: str | None = None
    actor_id: str | None = None
    integration_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DispatchResult(BaseModel):
    """Result returned by a runtime adapter after dispatching a run."""

    status: str  # "dispatched", "failed", "loopback"
    external_reference: str | None = None
    summary: str = ""
    raw_response: dict[str, Any] = Field(default_factory=dict)


class RunStatusResult(BaseModel):
    """Result of querying run status from a runtime substrate."""

    run_id: str
    status: str
    current_step: str | None = None
    detail: str = ""
    raw_payload: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------

class CanonicalDeploymentRequest(BaseModel):
    """Payload sent to a deployment adapter to execute a promotion."""

    promotion_id: str
    request_id: str
    target: str
    strategy: str
    integration_id: str | None = None
    actor_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeploymentResult(BaseModel):
    """Result returned by a deployment adapter."""

    status: str  # "success", "failed", "pending"
    external_reference: str | None = None
    summary: str = ""
    raw_response: dict[str, Any] = Field(default_factory=dict)


class DeploymentStatusResult(BaseModel):
    """Result of querying deployment status from a substrate."""

    deployment_id: str
    status: str
    detail: str = ""
    raw_payload: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Canonical event
# ---------------------------------------------------------------------------

class CanonicalEvent(BaseModel):
    """Substrate-neutral event representation.

    All events from external systems are normalized into this form before
    being ingested into the RGP event store.
    """

    tenant_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    timestamp: datetime
    actor: str
    detail: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    # Optional linkage
    request_id: str | None = None
    run_id: str | None = None
    artifact_id: str | None = None
    promotion_id: str | None = None
    check_run_id: str | None = None

    # Raw substrate payload preserved for audit
    raw_substrate_event: dict[str, Any] | None = None
    substrate_source: str | None = None
