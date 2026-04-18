"""Adapter protocol contracts for substrate abstraction.

External systems (runtimes, deployment targets, event sources) are accessed
through these protocols.  Concrete adapters implement the protocol for each
substrate type (HTTP, Foundry, Git, CMS, etc.).
"""

from __future__ import annotations

from typing import Protocol

from app.domain.substrate.canonical import (
    CanonicalDeploymentRequest,
    CanonicalEvent,
    CanonicalRunDispatch,
    DeploymentResult,
    DeploymentStatusResult,
    DispatchResult,
    RunStatusResult,
)


class RuntimeAdapter(Protocol):
    """Contract for dispatching and querying runs on an external runtime."""

    def dispatch_run(self, payload: CanonicalRunDispatch) -> DispatchResult:
        """Dispatch a run to the runtime substrate."""
        ...

    def query_run_status(self, external_ref: str) -> RunStatusResult:
        """Query the current status of a previously dispatched run."""
        ...


class DeploymentAdapter(Protocol):
    """Contract for executing and querying deployments on a target substrate."""

    def execute_deployment(self, payload: CanonicalDeploymentRequest) -> DeploymentResult:
        """Execute a deployment on the target substrate."""
        ...

    def query_deployment_status(self, external_ref: str) -> DeploymentStatusResult:
        """Query the current status of a previously executed deployment."""
        ...


class GovernedSessionRuntimeAdapter(RuntimeAdapter, Protocol):
    """Contract for stateful governed runtimes that expose durable session semantics."""

    def resume_session(self, session_ref: str, *, approval_token: str | None = None) -> dict:
        """Resume a previously paused governed runtime session."""
        ...

    def approve_operation(self, session_ref: str, operation_ref: str) -> dict:
        """Approve a governed runtime checkpoint or operation."""
        ...

    def list_artifacts(self, session_ref: str) -> list[dict]:
        """Return importable artifacts visible to the governed runtime session."""
        ...


class EventSink(Protocol):
    """Contract for emitting canonical events to an external sink."""

    def emit(self, event: CanonicalEvent) -> None:
        """Emit a single canonical event."""
        ...

    def emit_batch(self, events: list[CanonicalEvent]) -> None:
        """Emit a batch of canonical events."""
        ...


class ProjectionAdapter(Protocol):
    """Contract for projecting RGP entities into external systems and querying back."""

    def project_entity(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        """Project an RGP entity into the external system. Returns external reference."""
        ...

    def query_external_state(self, external_ref: str) -> dict:
        """Query the current state of a projected entity in the external system."""
        ...

    def reconcile(self, entity_data: dict, external_state: dict) -> dict:
        """Compare RGP state with external state and return reconciliation result."""
        ...
