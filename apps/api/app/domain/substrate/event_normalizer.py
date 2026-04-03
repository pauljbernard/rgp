"""Event normalization — translate raw substrate events into canonical form."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.substrate.canonical import CanonicalEvent


def normalize_from_event_store_row(row) -> CanonicalEvent:
    """Convert an ``EventStoreTable`` row into a ``CanonicalEvent``."""
    return CanonicalEvent(
        tenant_id=row.tenant_id or "system",
        event_type=row.event_type or "",
        aggregate_type=row.aggregate_type or "",
        aggregate_id=row.aggregate_id or "",
        timestamp=row.occurred_at or datetime.now(timezone.utc),
        actor=row.actor or "",
        detail=row.detail or "",
        payload=row.payload or {},
        request_id=row.request_id,
        run_id=row.run_id,
        artifact_id=row.artifact_id,
        promotion_id=row.promotion_id,
        check_run_id=row.check_run_id,
    )


def normalize_from_runtime_signal(signal_row) -> CanonicalEvent:
    """Convert a ``RuntimeSignalTable`` row into a ``CanonicalEvent``."""
    return CanonicalEvent(
        tenant_id=signal_row.tenant_id or "system",
        event_type=f"runtime.signal.{signal_row.status or 'unknown'}",
        aggregate_type="run",
        aggregate_id=signal_row.run_id or "",
        timestamp=signal_row.received_at or datetime.now(timezone.utc),
        actor=signal_row.source or "runtime",
        detail=signal_row.detail or "",
        payload=signal_row.payload or {},
        request_id=signal_row.request_id,
        run_id=signal_row.run_id,
        raw_substrate_event=signal_row.payload,
        substrate_source=signal_row.source,
    )
