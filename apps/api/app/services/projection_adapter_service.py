"""Projection adapter service for federated projection sync.

Provides adapter-backed projection and external-state sync behavior. The local
environment still uses governed mock substrate behavior, but adapter selection
now follows the integration's declared substrate/provider so federation
surfaces no longer collapse into a single generic adapter type.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import IntegrationTable


@dataclass(frozen=True)
class ProjectionAdapterSnapshot:
    adapter_type: str
    capabilities: list[str]
    external_state: dict


class BaseProjectionAdapter:
    adapter_type = "projection"
    capabilities = [
        "project",
        "query_external_state",
        "reconcile",
        "capability_discovery",
    ]

    def project_entity(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        shadow = self._shadow(entity_type, entity_id, entity_data)
        shadow["last_projected_at"] = now
        shadow.setdefault("activity_log", []).append(
            {"at": now, "event": "projected", "adapter_type": self.adapter_type, "entity_id": entity_id}
        )
        return {
            "status": shadow.get("status"),
            "title": shadow.get("title"),
            "sync_source": f"adapter:{self.adapter_type}",
            "adapter_type": self.adapter_type,
            "adapter_capabilities": list(self.capabilities),
            "_adapter_shadow": shadow,
        }

    def query_external_state(self, external_ref: str, current_state: dict, canonical_state: dict) -> ProjectionAdapterSnapshot:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        shadow = dict((current_state or {}).get("_adapter_shadow") or {})
        if not shadow:
            shadow = self._shadow(canonical_state.get("entity_type", "unknown"), canonical_state.get("id", external_ref), canonical_state)
        shadow["external_ref"] = external_ref
        shadow["last_synced_at"] = now
        shadow.setdefault("activity_log", []).append(
            {"at": now, "event": "synced", "adapter_type": self.adapter_type, "external_ref": external_ref}
        )
        projected_shape = {
            key: value
            for key, value in shadow.items()
            if key
            not in {
                "status",
                "title",
                "entity_type",
                "entity_id",
                "adapter_type",
                "external_ref",
                "last_synced_at",
                "last_projected_at",
            }
        }
        return ProjectionAdapterSnapshot(
            adapter_type=self.adapter_type,
            capabilities=list(self.capabilities),
            external_state={
                "status": shadow.get("status"),
                "title": shadow.get("title"),
                "sync_source": f"adapter:{self.adapter_type}",
                "adapter_type": self.adapter_type,
                "adapter_capabilities": list(self.capabilities),
                "external_ref": external_ref,
                **projected_shape,
                "_adapter_shadow": shadow,
            },
        )

    def apply_resolution(self, action: str, current_state: dict, canonical_state: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        next_state = dict(current_state or {})
        if action == "accept_internal":
            next_state.update(canonical_state)
        elif action == "accept_external":
            next_state["accepted_at"] = now
        next_state["resolution_basis"] = action
        next_state["resolution_profile"] = self.adapter_type
        shadow = dict(next_state.get("_adapter_shadow") or {})
        shadow.setdefault("activity_log", []).append(
            {"at": now, "event": f"resolution:{action}", "adapter_type": self.adapter_type}
        )
        next_state["_adapter_shadow"] = shadow
        return next_state

    def _shadow(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        return {
            "status": entity_data.get("status", "pending"),
            "title": entity_data.get("title"),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "adapter_type": self.adapter_type,
            "activity_log": [],
        }


class RepositoryProjectionAdapter(BaseProjectionAdapter):
    adapter_type = "repository_projection"
    capabilities = [
        "project",
        "query_external_state",
        "reconcile",
        "capability_discovery",
        "project_change_set",
        "project_review",
    ]

    def _shadow(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        title = entity_data.get("title")
        status = entity_data.get("status", "pending")
        slug = entity_id.replace("_", "-")
        return {
            "status": status,
            "title": title,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "adapter_type": self.adapter_type,
            "repository_state": {
                "branch": f"rgp/{slug}",
                "change_ref": f"refs/heads/rgp/{slug}",
                "review_state": "open" if status not in {"completed", "approved"} else "merged",
                "mergeability": "blocked" if status in {"changes_requested", "failed"} else "ready",
            },
            "projection_form": "change_set",
        }

    def apply_resolution(self, action: str, current_state: dict, canonical_state: dict) -> dict:
        next_state = super().apply_resolution(action, current_state, canonical_state)
        repository_state = dict(next_state.get("repository_state") or {})
        shadow = dict(next_state.get("_adapter_shadow") or {})
        activity_log = list(shadow.get("activity_log") or [])
        if action == "merge":
            repository_state["review_state"] = "merged"
            repository_state["mergeability"] = "merged"
            repository_state["merged_change_ref"] = repository_state.get("change_ref")
            repository_state["last_commit_sha"] = f"sha_{canonical_state.get('id', 'projection')[-8:]}"
            repository_state["merge_ticket"] = f"mr_{canonical_state.get('id', 'projection')[-8:]}"
            next_state.update(canonical_state)
            next_state["merged_fields"] = sorted({"status", "title"} & set(next_state.keys() | canonical_state.keys()))
            activity_log.append({"event": "merge_requested", "change_ref": repository_state.get("change_ref")})
        elif action == "accept_internal":
            repository_state["review_state"] = "governed"
            activity_log.append({"event": "governed_state_accepted"})
        elif action == "accept_external":
            repository_state["review_state"] = "external_authoritative"
            activity_log.append({"event": "external_state_accepted"})
        next_state["repository_state"] = repository_state
        shadow["repository_state"] = repository_state
        shadow["activity_log"] = activity_log
        next_state["_adapter_shadow"] = shadow
        return next_state

    def query_external_state(self, external_ref: str, current_state: dict, canonical_state: dict) -> ProjectionAdapterSnapshot:
        snapshot = super().query_external_state(external_ref, current_state, canonical_state)
        repository_state = dict(snapshot.external_state.get("repository_state") or {})
        if (current_state or {}).get("resolution_basis") == "merge":
            repository_state["remote_merge_state"] = "confirmed"
            repository_state["review_state"] = "merged"
        snapshot.external_state["repository_state"] = repository_state
        return snapshot


class RuntimeProjectionAdapter(BaseProjectionAdapter):
    adapter_type = "runtime_projection"
    capabilities = [
        "project",
        "query_external_state",
        "reconcile",
        "capability_discovery",
        "project_execution_state",
        "project_runtime_signal",
    ]

    def _shadow(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        status = entity_data.get("status", "pending")
        return {
            "status": status,
            "title": entity_data.get("title"),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "adapter_type": self.adapter_type,
            "runtime_state": {
                "execution_status": "running" if status in {"queued", "in_execution"} else "idle",
                "target_environment": "governed-runtime",
                "last_signal": "accepted_for_execution" if status in {"submitted", "queued", "in_execution"} else "awaiting_dispatch",
            },
            "projection_form": "execution_binding",
        }

    def query_external_state(self, external_ref: str, current_state: dict, canonical_state: dict) -> ProjectionAdapterSnapshot:
        snapshot = super().query_external_state(external_ref, current_state, canonical_state)
        runtime_state = dict(snapshot.external_state.get("runtime_state") or {})
        if (current_state or {}).get("resolution_basis") == "retry_sync":
            runtime_state["execution_status"] = "resync_in_progress"
            runtime_state["last_signal"] = "retry_acknowledged"
        snapshot.external_state["runtime_state"] = runtime_state
        return snapshot

    def apply_resolution(self, action: str, current_state: dict, canonical_state: dict) -> dict:
        next_state = super().apply_resolution(action, current_state, canonical_state)
        runtime_state = dict(next_state.get("runtime_state") or {})
        shadow = dict(next_state.get("_adapter_shadow") or {})
        activity_log = list(shadow.get("activity_log") or [])
        if action == "retry_sync":
            runtime_state["execution_status"] = "retry_requested"
            runtime_state["last_signal"] = "retry_requested"
            runtime_state["retry_attempt"] = int(runtime_state.get("retry_attempt") or 0) + 1
            runtime_state["recovery_ticket"] = f"rt_{canonical_state.get('id', 'projection')[-8:]}"
            next_state["retry_requested_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            activity_log.append({"event": "retry_requested", "retry_attempt": runtime_state["retry_attempt"]})
        next_state["runtime_state"] = runtime_state
        shadow["runtime_state"] = runtime_state
        shadow["activity_log"] = activity_log
        next_state["_adapter_shadow"] = shadow
        return next_state


class IdentityProjectionAdapter(BaseProjectionAdapter):
    adapter_type = "identity_projection"
    capabilities = [
        "project",
        "query_external_state",
        "reconcile",
        "capability_discovery",
        "project_identity_binding",
    ]

    def _shadow(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        status = entity_data.get("status", "pending")
        return {
            "status": status,
            "title": entity_data.get("title"),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "adapter_type": self.adapter_type,
            "identity_state": {
                "account_status": "provisioned" if status in {"approved", "completed"} else "pending",
                "provisioning_state": "ready_for_activation" if status == "approved" else "awaiting_governance",
                "mapped_roles": ["submitter"],
            },
            "projection_form": "identity_binding",
        }

    def query_external_state(self, external_ref: str, current_state: dict, canonical_state: dict) -> ProjectionAdapterSnapshot:
        snapshot = super().query_external_state(external_ref, current_state, canonical_state)
        identity_state = dict(snapshot.external_state.get("identity_state") or {})
        if (current_state or {}).get("resolution_basis") == "reprovision":
            identity_state["provisioning_state"] = "reprovision_requested"
        snapshot.external_state["identity_state"] = identity_state
        return snapshot

    def apply_resolution(self, action: str, current_state: dict, canonical_state: dict) -> dict:
        next_state = super().apply_resolution(action, current_state, canonical_state)
        identity_state = dict(next_state.get("identity_state") or {})
        shadow = dict(next_state.get("_adapter_shadow") or {})
        activity_log = list(shadow.get("activity_log") or [])
        if action == "reprovision":
            next_state.update(canonical_state)
            identity_state["provisioning_state"] = "reprovision_requested"
            identity_state["account_status"] = "provisioned"
            identity_state["reprovision_ticket"] = f"idm_{canonical_state.get('id', 'projection')[-8:]}"
            identity_state["last_reconciled_roles"] = list(identity_state.get("mapped_roles") or [])
            activity_log.append({"event": "reprovision_requested", "ticket": identity_state["reprovision_ticket"]})
        next_state["identity_state"] = identity_state
        shadow["identity_state"] = identity_state
        shadow["activity_log"] = activity_log
        next_state["_adapter_shadow"] = shadow
        return next_state


class AgentProjectionAdapter(BaseProjectionAdapter):
    adapter_type = "agent_projection"
    capabilities = [
        "project",
        "query_external_state",
        "reconcile",
        "capability_discovery",
        "project_agent_session",
        "project_context_binding",
    ]

    def _shadow(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        status = entity_data.get("status", "pending")
        return {
            "status": status,
            "title": entity_data.get("title"),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "adapter_type": self.adapter_type,
            "agent_state": {
                "session_status": "active" if status in {"awaiting_input", "in_execution", "under_review"} else "standby",
                "interaction_mode": "interactive",
                "context_binding": "governed",
            },
            "projection_form": "agent_session",
        }

    def query_external_state(self, external_ref: str, current_state: dict, canonical_state: dict) -> ProjectionAdapterSnapshot:
        snapshot = super().query_external_state(external_ref, current_state, canonical_state)
        agent_state = dict(snapshot.external_state.get("agent_state") or {})
        if (current_state or {}).get("resolution_basis") == "resume_session":
            agent_state["session_status"] = "resume_requested"
        snapshot.external_state["agent_state"] = agent_state
        return snapshot

    def apply_resolution(self, action: str, current_state: dict, canonical_state: dict) -> dict:
        next_state = super().apply_resolution(action, current_state, canonical_state)
        agent_state = dict(next_state.get("agent_state") or {})
        shadow = dict(next_state.get("_adapter_shadow") or {})
        activity_log = list(shadow.get("activity_log") or [])
        if action == "resume_session":
            agent_state["session_status"] = "resume_requested"
            agent_state["interaction_mode"] = "interactive"
            agent_state["resume_ticket"] = f"agt_{canonical_state.get('id', 'projection')[-8:]}"
            agent_state["last_context_refresh"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            next_state["resume_requested_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            activity_log.append({"event": "resume_requested", "ticket": agent_state["resume_ticket"]})
        next_state["agent_state"] = agent_state
        shadow["agent_state"] = agent_state
        shadow["activity_log"] = activity_log
        next_state["_adapter_shadow"] = shadow
        return next_state


class SbclAgentProjectionAdapter(AgentProjectionAdapter):
    adapter_type = "sbcl_agent_projection"
    capabilities = AgentProjectionAdapter.capabilities + [
        "project_environment",
        "project_thread",
        "project_turn",
        "project_operation",
        "project_artifact",
        "resume_runtime",
        "approve_runtime_checkpoint",
        "import_runtime_artifact",
    ]

    def _shadow(self, entity_type: str, entity_id: str, entity_data: dict) -> dict:
        shadow = super()._shadow(entity_type, entity_id, entity_data)
        governed_runtime = dict(entity_data.get("governed_runtime") or {})
        shadow["projection_form"] = "sbcl_agent_runtime"
        shadow["binding"] = dict(entity_data.get("binding") or {})
        shadow["governed_runtime"] = governed_runtime
        shadow["approvals"] = list(entity_data.get("approvals") or [])
        shadow["artifacts"] = list(entity_data.get("artifacts") or [])
        shadow["agent_state"] = {
            **dict(shadow.get("agent_state") or {}),
            "session_status": entity_data.get("session_status", "active"),
            "runtime_subtype": governed_runtime.get("runtime_subtype", "sbcl_agent"),
            "session_kind": governed_runtime.get("session_kind", "stateful_runtime"),
            "environment_ref": entity_data.get("environment_ref") or governed_runtime.get("environment_ref"),
            "thread_ref": entity_data.get("thread_ref") or governed_runtime.get("thread_ref"),
            "turn_ref": entity_data.get("turn_ref") or governed_runtime.get("turn_ref"),
            "operation_count": entity_data.get("operation_count", len(entity_data.get("operations") or [])),
            "artifact_count": entity_data.get("artifact_count", len(entity_data.get("artifacts") or [])),
            "pending_approval_count": governed_runtime.get("pending_approval_count", len(entity_data.get("approvals") or [])),
        }
        shadow["governed_entities"] = entity_data.get("governed_entities", [])
        return shadow

    def apply_resolution(self, action: str, current_state: dict, canonical_state: dict) -> dict:
        next_state = super().apply_resolution(action, current_state, canonical_state)
        agent_state = dict(next_state.get("agent_state") or {})
        if action == "resume_runtime":
            agent_state["session_status"] = "resume_requested"
            next_state["resume_requested_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        elif action == "approve_runtime_checkpoint":
            agent_state["checkpoint_state"] = "approved"
            next_state["approval_recorded_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        elif action == "import_runtime_artifact":
            next_state["artifact_import_status"] = "requested"
        next_state["agent_state"] = agent_state
        return next_state


class OpenAiProjectionAdapter(AgentProjectionAdapter):
    adapter_type = "openai_projection"


class AnthropicProjectionAdapter(AgentProjectionAdapter):
    adapter_type = "anthropic_projection"


class MicrosoftProjectionAdapter(AgentProjectionAdapter):
    adapter_type = "microsoft_projection"


class GenericProjectionAdapter(BaseProjectionAdapter):
    adapter_type = "generic_projection"


class ProjectionAdapterService:
    def resolve_adapter(self, integration: IntegrationTable) -> BaseProjectionAdapter:
        integration_type = (integration.type or "").strip().lower()
        provider = self._provider(integration)

        if provider == "openai":
            return OpenAiProjectionAdapter()
        if provider == "anthropic":
            return AnthropicProjectionAdapter()
        if provider == "microsoft" and integration_type == "agent_runtime":
            return MicrosoftProjectionAdapter()

        if integration_type == "repository":
            return RepositoryProjectionAdapter()
        if integration_type in {"runtime", "deployment"}:
            return RuntimeProjectionAdapter()
        if integration_type == "identity":
            return IdentityProjectionAdapter()
        if integration_type == "agent_runtime":
            runtime_subtype = ((integration.settings or {}).get("runtime_subtype") or "").strip().lower()
            if runtime_subtype == "sbcl_agent":
                return SbclAgentProjectionAdapter()
            return AgentProjectionAdapter()
        return GenericProjectionAdapter()

    def resolve_adapter_by_type(self, adapter_type: str | None) -> BaseProjectionAdapter:
        mapping = {
            "repository_projection": RepositoryProjectionAdapter,
            "runtime_projection": RuntimeProjectionAdapter,
            "identity_projection": IdentityProjectionAdapter,
            "agent_projection": AgentProjectionAdapter,
            "openai_projection": OpenAiProjectionAdapter,
            "anthropic_projection": AnthropicProjectionAdapter,
            "microsoft_projection": MicrosoftProjectionAdapter,
            "generic_projection": GenericProjectionAdapter,
        }
        factory = mapping.get(adapter_type or "", GenericProjectionAdapter)
        return factory()

    @staticmethod
    def _provider(integration: IntegrationTable) -> str | None:
        settings = integration.settings if isinstance(integration.settings, dict) else {}
        configured = settings.get("provider")
        if isinstance(configured, str) and configured.strip():
            return configured.strip().lower()
        return None


projection_adapter_service = ProjectionAdapterService()
