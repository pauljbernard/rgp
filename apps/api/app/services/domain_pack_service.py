"""Domain pack service -- lifecycle management for domain packs and installations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import DomainPackTable, DomainPackInstallationTable
from app.db.session import SessionLocal
from app.models.domain_pack import (
    CreateDomainPackRequest,
    DomainPackComparison,
    DomainPackContributionDelta,
    DomainPackDetail,
    DomainPackInstallation,
    DomainPackLineageEntry,
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

    def list_installations(self, pack_id: str, tenant_id: str) -> list[DomainPackInstallation]:
        with SessionLocal() as session:
            rows = (
                session.query(DomainPackInstallationTable)
                .filter(
                    DomainPackInstallationTable.pack_id == pack_id,
                    DomainPackInstallationTable.tenant_id == tenant_id,
                )
                .order_by(DomainPackInstallationTable.installed_at.desc())
                .all()
            )
            return [DomainPackInstallation.model_validate(r) for r in rows]

    def get_pack_detail(self, pack_id: str, tenant_id: str) -> DomainPackDetail:
        pack = self.get_pack(pack_id)
        if pack.tenant_id != tenant_id:
            raise ValueError("Pack not found")
        return DomainPackDetail(
            pack=pack,
            installations=self.list_installations(pack_id, tenant_id),
        )

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

    def compare_pack(self, pack_id: str, tenant_id: str) -> DomainPackComparison:
        with SessionLocal() as session:
            row = (
                session.query(DomainPackTable)
                .filter(
                    DomainPackTable.id == pack_id,
                    DomainPackTable.tenant_id == tenant_id,
                )
                .one()
            )
            baseline = (
                session.query(DomainPackTable)
                .filter(
                    DomainPackTable.tenant_id == tenant_id,
                    DomainPackTable.name == row.name,
                    DomainPackTable.id != row.id,
                )
                .order_by(DomainPackTable.created_at.desc())
                .first()
            )

            categories = (
                ("templates", row.contributed_templates or [], baseline.contributed_templates if baseline else []),
                ("artifact_types", row.contributed_artifact_types or [], baseline.contributed_artifact_types if baseline else []),
                ("workflows", row.contributed_workflows or [], baseline.contributed_workflows if baseline else []),
                ("policies", row.contributed_policies or [], baseline.contributed_policies if baseline else []),
            )
            deltas: list[DomainPackContributionDelta] = []
            total_added = 0
            total_removed = 0
            for category, current_items, baseline_items in categories:
                added = sorted(set(current_items) - set(baseline_items))
                removed = sorted(set(baseline_items) - set(current_items))
                total_added += len(added)
                total_removed += len(removed)
                deltas.append(
                    DomainPackContributionDelta(
                        category=category,
                        added=added,
                        removed=removed,
                    )
                )

            if baseline is None:
                summary = "No prior version exists for comparison."
            elif total_added == 0 and total_removed == 0:
                summary = "This version carries the same declared contributions as the previous version."
            else:
                summary = f"Compared with {baseline.version}: {total_added} additions and {total_removed} removals across declared contributions."

            return DomainPackComparison(
                current_pack_id=row.id,
                current_version=row.version,
                baseline_pack_id=baseline.id if baseline else None,
                baseline_version=baseline.version if baseline else None,
                deltas=deltas,
                summary=summary,
            )

    def list_pack_lineage(self, pack_id: str, tenant_id: str) -> list[DomainPackLineageEntry]:
        with SessionLocal() as session:
            row = (
                session.query(DomainPackTable)
                .filter(
                    DomainPackTable.id == pack_id,
                    DomainPackTable.tenant_id == tenant_id,
                )
                .one()
            )
            related = (
                session.query(DomainPackTable)
                .filter(
                    DomainPackTable.tenant_id == tenant_id,
                    DomainPackTable.name == row.name,
                )
                .order_by(DomainPackTable.created_at.desc())
                .all()
            )
            return [
                DomainPackLineageEntry(
                    pack_id=item.id,
                    version=item.version,
                    status=item.status,
                    created_at=item.created_at,
                    activated_at=item.activated_at,
                    contribution_count=len(item.contributed_templates or [])
                    + len(item.contributed_artifact_types or [])
                    + len(item.contributed_workflows or [])
                    + len(item.contributed_policies or []),
                )
                for item in related
            ]


domain_pack_service = DomainPackService()
