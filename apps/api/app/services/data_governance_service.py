"""Data governance service -- classification, retention policies, and lineage tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func

from app.db.models import DataClassificationTable, RetentionPolicyTable, DataLineageTable
from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service


# ---------------------------------------------------------------------------
# Lightweight record models (Pydantic-free dicts for now; swap to pydantic
# records when the models/ layer adds them).
# ---------------------------------------------------------------------------

class _Record(dict):
    """Thin dict subclass that allows attribute access for convenience."""
    __getattr__ = dict.__getitem__


def _classification_record(row: DataClassificationTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "classification_level": row.classification_level,
        "residency_zone": row.residency_zone,
        "retention_policy_id": row.retention_policy_id,
        "classified_by": row.classified_by,
        "classified_at": row.classified_at.isoformat() if row.classified_at else None,
    }


def _retention_policy_record(row: RetentionPolicyTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "retention_days": row.retention_days,
        "action_on_expiry": row.action_on_expiry,
        "applies_to": row.applies_to,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _lineage_record(row: DataLineageTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "source_type": row.source_type,
        "source_id": row.source_id,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "transformation": row.transformation,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class DataGovernanceService:
    """Manages data classification, retention policies, and data lineage."""

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify_entity(
        self,
        entity_type: str,
        entity_id: str,
        level: str,
        residency_zone: str | None,
        retention_policy_id: str | None,
        actor_id: str,
        tenant_id: str,
    ) -> dict:
        """Create or update a data classification for a given entity."""
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            existing = (
                session.query(DataClassificationTable)
                .filter(
                    DataClassificationTable.tenant_id == tenant_id,
                    DataClassificationTable.entity_type == entity_type,
                    DataClassificationTable.entity_id == entity_id,
                )
                .first()
            )

            if existing:
                existing.classification_level = level
                existing.residency_zone = residency_zone
                existing.retention_policy_id = retention_policy_id
                existing.classified_by = actor_id
                existing.classified_at = now
                session.flush()
                record = _classification_record(existing)
            else:
                row = DataClassificationTable(
                    id=f"dc_{uuid4().hex[:12]}",
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    classification_level=level,
                    residency_zone=residency_zone,
                    retention_policy_id=retention_policy_id,
                    classified_by=actor_id,
                    classified_at=now,
                )
                session.add(row)
                session.flush()
                record = _classification_record(row)

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="data_governance.entity_classified",
                aggregate_type="data_classification",
                aggregate_id=record["id"],
                actor=actor_id,
                detail=f"Entity {entity_type}/{entity_id} classified as {level}",
            )
            session.commit()
            return record

    def get_classification(
        self, entity_type: str, entity_id: str, tenant_id: str
    ) -> dict | None:
        """Return the current classification for an entity, or None."""
        with SessionLocal() as session:
            row = (
                session.query(DataClassificationTable)
                .filter(
                    DataClassificationTable.tenant_id == tenant_id,
                    DataClassificationTable.entity_type == entity_type,
                    DataClassificationTable.entity_id == entity_id,
                )
                .first()
            )
            return _classification_record(row) if row else None

    # ------------------------------------------------------------------
    # Retention policies
    # ------------------------------------------------------------------

    def create_retention_policy(
        self,
        name: str,
        retention_days: int,
        action_on_expiry: str,
        applies_to: list[str],
        tenant_id: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        policy_id = f"rp_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = RetentionPolicyTable(
                id=policy_id,
                tenant_id=tenant_id,
                name=name,
                retention_days=retention_days,
                action_on_expiry=action_on_expiry,
                applies_to=applies_to,
                status="active",
                created_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="data_governance.retention_policy_created",
                aggregate_type="retention_policy",
                aggregate_id=policy_id,
                actor="system",
                detail=f"Retention policy '{name}' created ({retention_days} days, {action_on_expiry})",
            )
            session.commit()
            session.refresh(row)
            return _retention_policy_record(row)

    def list_retention_policies(self, tenant_id: str) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(RetentionPolicyTable)
                .filter(RetentionPolicyTable.tenant_id == tenant_id)
                .order_by(RetentionPolicyTable.created_at.desc())
                .all()
            )
            return [_retention_policy_record(r) for r in rows]

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------

    def record_lineage(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        transformation: str | None,
        tenant_id: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        lineage_id = f"dl_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = DataLineageTable(
                id=lineage_id,
                tenant_id=tenant_id,
                source_type=source_type,
                source_id=source_id,
                target_type=target_type,
                target_id=target_id,
                transformation=transformation,
                created_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="data_governance.lineage_recorded",
                aggregate_type="data_lineage",
                aggregate_id=lineage_id,
                actor="system",
                detail=f"Lineage: {source_type}/{source_id} -> {target_type}/{target_id}",
            )
            session.commit()
            session.refresh(row)
            return _lineage_record(row)

    def get_lineage(
        self, entity_type: str, entity_id: str, tenant_id: str
    ) -> list[dict]:
        """Return all lineage records where the entity appears as source or target."""
        with SessionLocal() as session:
            rows = (
                session.query(DataLineageTable)
                .filter(
                    DataLineageTable.tenant_id == tenant_id,
                    (
                        (DataLineageTable.source_type == entity_type)
                        & (DataLineageTable.source_id == entity_id)
                    )
                    | (
                        (DataLineageTable.target_type == entity_type)
                        & (DataLineageTable.target_id == entity_id)
                    ),
                )
                .order_by(DataLineageTable.created_at.asc())
                .all()
            )
            return [_lineage_record(r) for r in rows]


data_governance_service = DataGovernanceService()
