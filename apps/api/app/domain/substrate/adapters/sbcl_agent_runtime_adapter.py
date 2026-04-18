"""Dedicated sbcl-agent substrate adapters.

These adapters keep sbcl-agent on the substrate side of the architecture:
RGP governs request state while sbcl-agent remains the specialized runtime.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.domain.substrate.canonical import (
    CanonicalDeploymentRequest,
    CanonicalRunDispatch,
    DeploymentResult,
    DeploymentStatusResult,
    DispatchResult,
    RunStatusResult,
)
from app.services.deployment_service import deployment_service
from app.services.runtime_dispatch_service import runtime_dispatch_service


class SbclAgentRuntimeAdapter:
    """Runtime adapter for governed sbcl-agent execution."""

    adapter_type = "sbcl_agent_runtime"
    session_kind = "stateful_runtime"
    runtime_subtype = "sbcl_agent"

    def _binding_payload(self, payload: CanonicalRunDispatch) -> dict:
        metadata = payload.metadata or {}
        return {
            "request_id": payload.request_id,
            "run_id": payload.run_id,
            "workflow_binding_id": payload.workflow_binding_id,
            "actor_id": payload.actor_id,
            "runtime_subtype": self.runtime_subtype,
            "session_kind": self.session_kind,
            "execution_model": "environment_first",
            "binding": {
                "request_id": payload.request_id,
                "agent_session_id": metadata.get("agent_session_id") or payload.run_id,
                "integration_id": payload.integration_id,
                "projection_id": metadata.get("projection_id"),
                "tenant_id": metadata.get("tenant_id"),
            },
            "projection_contract": {
                "projection_types": ["environment", "thread", "turn", "operation", "artifact"],
                "artifact_import_rule": "sbcl_agent_governed_runtime",
                "approval_action": "approve_runtime_checkpoint",
                "resume_action": "resume_runtime",
            },
        }

    def dispatch_run(self, payload: CanonicalRunDispatch) -> DispatchResult:
        integration = self._resolve_integration(payload.integration_id)
        response = runtime_dispatch_service.dispatch(
            integration=integration,
            request_id=payload.request_id,
            run_id=payload.run_id,
            payload=self._binding_payload(payload),
        )
        return DispatchResult(
            status="dispatched",
            external_reference=response.get("external_reference") or f"sbcl-agent:{payload.run_id}",
            summary=response.get("summary", "sbcl-agent governed runtime dispatch accepted"),
            raw_response={
                "runtime_subtype": self.runtime_subtype,
                "session_kind": self.session_kind,
                "dispatch_contract": "governed_runtime_binding",
                **({"response": response} if response else {}),
            },
        )

    def query_run_status(self, external_ref: str) -> RunStatusResult:
        snapshot = runtime_dispatch_service.export_sbcl_agent_snapshot(external_ref)
        governed_runtime = snapshot.get("governed_runtime") or {}
        approvals = snapshot.get("approvals") or []
        artifacts = snapshot.get("artifacts") or []
        return RunStatusResult(
            run_id=external_ref,
            status="waiting_on_human" if approvals else "running",
            current_step="governed_runtime",
            detail=f"sbcl-agent governed runtime binding active for {external_ref}",
            raw_payload={
                "binding": snapshot.get("binding") or {"external_ref": external_ref},
                "governed_runtime": {
                    "runtime_subtype": governed_runtime.get("runtime_subtype", self.runtime_subtype),
                    "session_kind": governed_runtime.get("session_kind", self.session_kind),
                    "supports_approval_actions": governed_runtime.get("supports_approval_actions_p", True),
                    "supports_resume_actions": governed_runtime.get("supports_resume_actions_p", True),
                    "supports_artifact_lineage": governed_runtime.get("supports_artifact_lineage_p", True),
                    **governed_runtime,
                },
                "approvals": approvals,
                "artifacts": artifacts,
                "resolution_actions": ["resume_runtime", "approve_runtime_checkpoint", "import_runtime_artifact"],
            },
        )

    def resume_session(self, session_ref: str, *, approval_token: str | None = None) -> dict:
        result = runtime_dispatch_service.resume_sbcl_agent_session(
            session_ref,
            approval_token or "runtime-work-item",
            note=approval_token,
        )
        return {
            "session_ref": session_ref,
            "action": "resume_runtime",
            "approval_token": approval_token,
            "status": result.get("status", "accepted"),
            "session_kind": self.session_kind,
            "runtime_subtype": self.runtime_subtype,
            "response": result,
        }

    def approve_operation(self, session_ref: str, operation_ref: str) -> dict:
        result = runtime_dispatch_service.approve_sbcl_agent_checkpoint(session_ref, operation_ref)
        return {
            "session_ref": session_ref,
            "operation_ref": operation_ref,
            "action": "approve_runtime_checkpoint",
            "status": result.get("status", "accepted"),
            "session_kind": self.session_kind,
            "runtime_subtype": self.runtime_subtype,
            "response": result,
        }

    def list_artifacts(self, session_ref: str) -> list[dict]:
        artifacts = runtime_dispatch_service.list_sbcl_agent_artifacts(session_ref)
        if artifacts:
            return artifacts
        return [
            {
                "session_ref": session_ref,
                "artifact_key": "runtime-summary",
                "title": "sbcl-agent runtime summary",
                "artifact_type": "sbcl_agent.runtime_summary",
                "import_rule": "sbcl_agent_governed_runtime",
                "lineage": {
                    "source_ref": session_ref,
                    "relation": "imported_from_sbcl_agent_session",
                },
            }
        ]

    @staticmethod
    def _resolve_integration(integration_id: str | None):
        from app.repositories.governance_repository import governance_repository

        if not integration_id:
            return SimpleNamespace(id="sbcl_agent", endpoint="sbcl://local-image", settings={"runtime_subtype": "sbcl_agent"})
        return next((item for item in governance_repository.list_integrations(None) if item.id == integration_id), SimpleNamespace(id=integration_id, endpoint="sbcl://local-image", settings={"runtime_subtype": "sbcl_agent"}))


class SbclAgentDeploymentAdapter:
    """Deployment adapter for sbcl-agent managed artifacts."""

    adapter_type = "sbcl_agent_deployment"

    def execute_deployment(self, payload: CanonicalDeploymentRequest) -> DeploymentResult:
        response = deployment_service.execute(
            integration=SimpleNamespace(id=payload.integration_id or "sbcl_agent", endpoint="sbcl://local-image", settings={"runtime_subtype": "sbcl_agent"}),
            request_id=payload.request_id,
            promotion_id=payload.promotion_id,
            target=payload.target,
            strategy=payload.strategy,
            payload={
                **payload.model_dump(mode="json"),
                "deployment_subtype": "sbcl_agent",
            },
        )
        return DeploymentResult(
            status="success",
            external_reference=response.get("external_reference") or f"sbcl-agent-deployment:{payload.promotion_id}",
            summary=response.get("summary", "sbcl-agent deployment accepted"),
            raw_response={
                "deployment_subtype": "sbcl_agent",
                "response": response,
            },
        )

    def query_deployment_status(self, external_ref: str) -> DeploymentStatusResult:
        return DeploymentStatusResult(
            deployment_id=external_ref,
            status="running",
            detail=f"sbcl-agent deployment binding active for {external_ref}",
            raw_payload={"deployment_subtype": "sbcl_agent"},
        )
