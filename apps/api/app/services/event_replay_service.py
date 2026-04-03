"""Event replay service -- replay events, manage checkpoints, and trace event lineage."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import EventStoreTable, EventReplayCheckpointTable
from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service


def _checkpoint_record(row: EventReplayCheckpointTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "replay_scope": row.replay_scope,
        "scope_id": row.scope_id,
        "last_event_id": row.last_event_id,
        "status": row.status,
        "replayed_at": row.replayed_at.isoformat() if row.replayed_at else None,
    }


def _event_dict(row: EventStoreTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "event_type": row.event_type,
        "aggregate_type": row.aggregate_type,
        "aggregate_id": row.aggregate_id,
        "request_id": row.request_id,
        "run_id": row.run_id,
        "artifact_id": row.artifact_id,
        "promotion_id": row.promotion_id,
        "check_run_id": row.check_run_id,
        "actor": row.actor,
        "detail": row.detail,
        "payload": row.payload,
        "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
    }


class EventReplayService:
    """Replay events from the event store with checkpoint management."""

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def replay_events(
        self,
        scope: str,
        scope_id: str,
        from_event_id: int | None,
        to_event_id: int | None,
        tenant_id: str,
    ) -> list[dict]:
        """Replay events for a given scope (e.g., 'request', 'run', 'tenant').

        Fetches events from the event store between the given event ID
        boundaries, filtered by scope. Returns the list of event dicts
        in chronological order.
        """
        with SessionLocal() as session:
            q = session.query(EventStoreTable).filter(
                EventStoreTable.tenant_id == tenant_id,
            )

            # Scope filtering: map scope to the appropriate column
            if scope == "request":
                q = q.filter(EventStoreTable.request_id == scope_id)
            elif scope == "run":
                q = q.filter(EventStoreTable.run_id == scope_id)
            elif scope == "artifact":
                q = q.filter(EventStoreTable.artifact_id == scope_id)
            elif scope == "promotion":
                q = q.filter(EventStoreTable.promotion_id == scope_id)
            elif scope == "aggregate":
                q = q.filter(EventStoreTable.aggregate_id == scope_id)
            # else: tenant-wide replay (no additional filter)

            if from_event_id is not None:
                q = q.filter(EventStoreTable.id >= from_event_id)
            if to_event_id is not None:
                q = q.filter(EventStoreTable.id <= to_event_id)

            rows = q.order_by(EventStoreTable.id.asc()).all()
            events = [_event_dict(r) for r in rows]

            # Auto-save checkpoint after successful replay
            if events:
                last_id = events[-1]["id"]
                self._upsert_checkpoint(session, scope, scope_id, last_id, tenant_id)
                session.commit()

            return events

    # ------------------------------------------------------------------
    # Checkpoints
    # ------------------------------------------------------------------

    def get_checkpoint(
        self, scope: str, scope_id: str, tenant_id: str
    ) -> dict | None:
        with SessionLocal() as session:
            row = (
                session.query(EventReplayCheckpointTable)
                .filter(
                    EventReplayCheckpointTable.tenant_id == tenant_id,
                    EventReplayCheckpointTable.replay_scope == scope,
                    EventReplayCheckpointTable.scope_id == scope_id,
                )
                .first()
            )
            return _checkpoint_record(row) if row else None

    def save_checkpoint(
        self, scope: str, scope_id: str, last_event_id: int, tenant_id: str
    ) -> dict:
        with SessionLocal() as session:
            row = self._upsert_checkpoint(session, scope, scope_id, last_event_id, tenant_id)
            session.commit()
            session.refresh(row)
            return _checkpoint_record(row)

    # ------------------------------------------------------------------
    # Event lineage
    # ------------------------------------------------------------------

    def get_event_lineage(self, event_id: int, tenant_id: str) -> list[dict]:
        """Trace the event chain by following the aggregate lineage.

        Given a starting event, finds all events sharing the same
        aggregate_type and aggregate_id up to and including the given event,
        providing a chronological chain of related events.
        """
        with SessionLocal() as session:
            seed = (
                session.query(EventStoreTable)
                .filter(
                    EventStoreTable.id == event_id,
                    EventStoreTable.tenant_id == tenant_id,
                )
                .first()
            )
            if not seed:
                return []

            chain = (
                session.query(EventStoreTable)
                .filter(
                    EventStoreTable.tenant_id == tenant_id,
                    EventStoreTable.aggregate_type == seed.aggregate_type,
                    EventStoreTable.aggregate_id == seed.aggregate_id,
                    EventStoreTable.id <= event_id,
                )
                .order_by(EventStoreTable.id.asc())
                .all()
            )
            return [_event_dict(r) for r in chain]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _upsert_checkpoint(
        self,
        session,
        scope: str,
        scope_id: str,
        last_event_id: int,
        tenant_id: str,
    ) -> EventReplayCheckpointTable:
        now = datetime.now(timezone.utc)
        row = (
            session.query(EventReplayCheckpointTable)
            .filter(
                EventReplayCheckpointTable.tenant_id == tenant_id,
                EventReplayCheckpointTable.replay_scope == scope,
                EventReplayCheckpointTable.scope_id == scope_id,
            )
            .first()
        )
        if row:
            row.last_event_id = last_event_id
            row.replayed_at = now
        else:
            row = EventReplayCheckpointTable(
                id=f"rc_{uuid4().hex[:12]}",
                tenant_id=tenant_id,
                replay_scope=scope,
                scope_id=scope_id,
                last_event_id=last_event_id,
                status="active",
                replayed_at=now,
            )
            session.add(row)
        session.flush()
        return row


event_replay_service = EventReplayService()
