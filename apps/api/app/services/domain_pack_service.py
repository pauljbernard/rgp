"""Domain pack service -- lifecycle management for domain packs and installations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import DomainPackTable, DomainPackInstallationTable
from app.db.session import SessionLocal
from app.models.domain_pack import (
    CreateDomainPackRequest,
    DomainPackInstallation,
    DomainPackRecord,
)
from app.services.event_store_service import event_store_service


class DomainPackService:
    """Manages domain pack registration, activation, and tenant installation."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_pack(
        self, payload: CreateDomainPackRequest, tenant_id: str
    ) -> DomainPackRecord:
        now = datetime.now(timezone.utc)
        pack_id = f"dp_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = DomainPackTable(
                id=pack_id,
                tenant_id=tenant_id,
                name=payload.name,
                version=payload.version,
                description=payload.description,
                status="draft",
                contributed_templates=payload.contributed_templates,
                contributed_artifact_types=payload.contributed_artifact_types,
                contributed_workflows=payload.contributed_workflows,
                contributed_policies=payload.contributed_policies,
                activated_at=None,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="domain_pack.created",
                aggregate_type="domain_pack",
                aggregate_id=pack_id,
                actor="system",
                detail=f"Domain pack '{payload.name}' v{payload.version} created",
            )
            session.commit()
            session.refresh(row)
            return DomainPackRecord.model_validate(row)

    def list_packs(self, tenant_id: str) -> list[DomainPackRecord]:
        with SessionLocal() as session:
            rows = (
                session.query(DomainPackTable)
                .filter(DomainPackTable.tenant_id == tenant_id)
                .order_by(DomainPackTable.created_at.desc())
                .all()
            )
            return [DomainPackRecord.model_validate(r) for r in rows]

    def get_pack(self, pack_id: str) -> DomainPackRecord:
        with SessionLocal() as session:
            row = (
                session.query(DomainPackTable)
                .filter(DomainPackTable.id == pack_id)
                .one()
            )
            return DomainPackRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def activate_pack(
        self, pack_id: str, actor_id: str, tenant_id: str
    ) -> DomainPackRecord:
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(DomainPackTable)
                .filter(
                    DomainPackTable.id == pack_id,
                    DomainPackTable.tenant_id == tenant_id,
                )
                .one()
            )
            row.status = "active"
            row.activated_at = now
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="domain_pack.activated",
                aggregate_type="domain_pack",
                aggregate_id=pack_id,
                actor=actor_id,
                detail=f"Domain pack '{row.name}' activated",
            )
            session.commit()
            session.refresh(row)
            return DomainPackRecord.model_validate(row)

    def deactivate_pack(
        self, pack_id: str, actor_id: str, tenant_id: str
    ) -> DomainPackRecord:
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(DomainPackTable)
                .filter(
                    DomainPackTable.id == pack_id,
                    DomainPackTable.tenant_id == tenant_id,
                )
                .one()
            )
            row.status = "deprecated"
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="domain_pack.deactivated",
                aggregate_type="domain_pack",
                aggregate_id=pack_id,
                actor=actor_id,
                detail=f"Domain pack '{row.name}' deprecated",
            )
            session.commit()
            session.refresh(row)
            return DomainPackRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Installation
    # ------------------------------------------------------------------

    def install_pack(
        self, pack_id: str, actor_id: str, tenant_id: str
    ) -> DomainPackInstallation:
        now = datetime.now(timezone.utc)
        install_id = f"dpi_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            pack = (
                session.query(DomainPackTable)
                .filter(DomainPackTable.id == pack_id)
                .one()
            )

            row = DomainPackInstallationTable(
                id=install_id,
                tenant_id=tenant_id,
                pack_id=pack_id,
                installed_version=pack.version,
                status="installed",
                installed_by=actor_id,
                installed_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="domain_pack.installed",
                aggregate_type="domain_pack",
                aggregate_id=pack_id,
                actor=actor_id,
                detail=f"Domain pack '{pack.name}' v{pack.version} installed",
            )
            session.commit()
            session.refresh(row)
            return DomainPackInstallation.model_validate(row)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_pack(self, pack_id: str) -> list[str]:
        """Return a list of validation errors for the domain pack.

        Checks core invariants such as: pack must have a name, at least
        one contribution, and a valid version string.
        """
        errors: list[str] = []

        with SessionLocal() as session:
            row = (
                session.query(DomainPackTable)
                .filter(DomainPackTable.id == pack_id)
                .one()
            )

            if not row.name or not row.name.strip():
                errors.append("Pack name is required")

            if not row.version or not row.version.strip():
                errors.append("Pack version is required")

            has_contributions = (
                bool(row.contributed_templates)
                or bool(row.contributed_artifact_types)
                or bool(row.contributed_workflows)
                or bool(row.contributed_policies)
            )
            if not has_contributions:
                errors.append("Pack must contribute at least one template, artifact type, workflow, or policy")

            # Check for duplicate contribution names within each category
            for field_name in (
                "contributed_templates",
                "contributed_artifact_types",
                "contributed_workflows",
                "contributed_policies",
            ):
                items = getattr(row, field_name) or []
                if len(items) != len(set(items)):
                    errors.append(f"Duplicate entries found in {field_name}")

        return errors


domain_pack_service = DomainPackService()
