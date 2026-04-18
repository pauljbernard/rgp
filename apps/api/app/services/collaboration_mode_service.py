"""Collaboration mode service — tracks and governs mode transitions.

Manages the lifecycle of collaboration modes (human_led, agent_assisted,
agent_led) on a per-request basis and emits governance events for each
transition.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import CollaborationModeTransitionTable
from app.db.session import SessionLocal
from app.models.collaboration import (
    CollaborationMode,
    ModeTransitionRecord,
    SwitchModeRequest,
)
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state

# Allowed directed transitions between collaboration modes.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    CollaborationMode.HUMAN_LED: {
        CollaborationMode.AGENT_ASSISTED,
    },
    CollaborationMode.AGENT_ASSISTED: {
        CollaborationMode.HUMAN_LED,
        CollaborationMode.AGENT_LED,
    },
    CollaborationMode.AGENT_LED: {
        CollaborationMode.AGENT_ASSISTED,
        CollaborationMode.HUMAN_LED,
    },
}


class CollaborationModeService:
    """Tracks collaboration mode on requests and governs transitions."""

    def get_current_mode(self, request_id: str, tenant_id: str) -> str:
        """Return the current collaboration mode for a request.

        If no transition has been recorded yet the default mode is
        ``human_led``.
        """
        with SessionLocal() as session:
            if get_request_state(request_id, tenant_id) is None:
                raise StopIteration(request_id)
            latest = (
                session.query(CollaborationModeTransitionTable)
                .filter(
                    CollaborationModeTransitionTable.request_id == request_id,
                    CollaborationModeTransitionTable.tenant_id == tenant_id,
                )
                .order_by(CollaborationModeTransitionTable.created_at.desc())
                .first()
            )
            if latest is None:
                return CollaborationMode.HUMAN_LED
            return latest.to_mode

    def switch_mode(
        self,
        request_id: str,
        payload: SwitchModeRequest,
        tenant_id: str,
    ) -> ModeTransitionRecord:
        """Validate and execute a collaboration mode transition.

        Raises ``ValueError`` if the transition is not allowed.
        """
        with SessionLocal() as session:
            if get_request_state(request_id, tenant_id) is None:
                raise StopIteration(request_id)

            current_mode = self.get_current_mode(request_id, tenant_id)
            target_mode = payload.target_mode.value

            if target_mode == current_mode:
                raise ValueError(
                    f"Request {request_id} is already in mode '{current_mode}'"
                )

            allowed = _ALLOWED_TRANSITIONS.get(current_mode, set())
            if target_mode not in allowed:
                raise ValueError(
                    f"Transition from '{current_mode}' to '{target_mode}' "
                    f"is not permitted"
                )

            now = datetime.now(timezone.utc)
            transition_id = f"cmt_{uuid.uuid4().hex[:12]}"

            row = CollaborationModeTransitionTable(
                id=transition_id,
                tenant_id=tenant_id,
                request_id=request_id,
                from_mode=current_mode,
                to_mode=target_mode,
                actor=payload.actor_id,
                reason=payload.reason or None,
                policy_basis=None,
                created_at=now,
            )
            session.add(row)

            # Emit governance event.
            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="collaboration_mode.switched",
                aggregate_type="request",
                aggregate_id=request_id,
                request_id=request_id,
                actor=payload.actor_id,
                detail=f"Mode switched from {current_mode} to {target_mode}",
                payload={
                    "from_mode": current_mode,
                    "to_mode": target_mode,
                    "reason": payload.reason,
                },
            )

            session.commit()
            session.refresh(row)
            return ModeTransitionRecord.model_validate(row)

    def list_transitions(
        self, request_id: str, tenant_id: str
    ) -> list[ModeTransitionRecord]:
        """Return the full transition history for a request."""
        with SessionLocal() as session:
            if get_request_state(request_id, tenant_id) is None:
                raise StopIteration(request_id)
            rows = (
                session.query(CollaborationModeTransitionTable)
                .filter(
                    CollaborationModeTransitionTable.request_id == request_id,
                    CollaborationModeTransitionTable.tenant_id == tenant_id,
                )
                .order_by(CollaborationModeTransitionTable.created_at)
                .all()
            )
            return [ModeTransitionRecord.model_validate(r) for r in rows]


collaboration_mode_service = CollaborationModeService()
