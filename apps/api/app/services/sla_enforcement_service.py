"""SLA enforcement service -- definitions, compliance evaluation, and breach recording."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import SlaDefinitionTable, SlaBreachAuditTable, RequestTable
from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service


def _sla_definition_record(row: SlaDefinitionTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "scope_type": row.scope_type,
        "scope_id": row.scope_id,
        "response_target_hours": row.response_target_hours,
        "resolution_target_hours": row.resolution_target_hours,
        "review_deadline_hours": row.review_deadline_hours,
        "warning_threshold_pct": row.warning_threshold_pct,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _breach_record(row: SlaBreachAuditTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "sla_definition_id": row.sla_definition_id,
        "request_id": row.request_id,
        "breach_type": row.breach_type,
        "target_hours": row.target_hours,
        "actual_hours": row.actual_hours,
        "severity": row.severity,
        "remediation_action": row.remediation_action,
        "breached_at": row.breached_at.isoformat() if row.breached_at else None,
    }


class SlaEnforcementService:
    """Manages SLA definitions, evaluates compliance, and records breaches."""

    # ------------------------------------------------------------------
    # SLA definitions
    # ------------------------------------------------------------------

    def create_sla_definition(
        self,
        name: str,
        scope_type: str,
        scope_id: str | None,
        response_hours: float | None,
        resolution_hours: float | None,
        review_hours: float | None,
        tenant_id: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        sla_id = f"sla_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = SlaDefinitionTable(
                id=sla_id,
                tenant_id=tenant_id,
                name=name,
                scope_type=scope_type,
                scope_id=scope_id,
                response_target_hours=response_hours,
                resolution_target_hours=resolution_hours,
                review_deadline_hours=review_hours,
                warning_threshold_pct=70,
                status="active",
                created_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="sla.definition_created",
                aggregate_type="sla_definition",
                aggregate_id=sla_id,
                actor="system",
                detail=f"SLA definition '{name}' created (scope: {scope_type})",
            )
            session.commit()
            session.refresh(row)
            return _sla_definition_record(row)

    def list_sla_definitions(self, tenant_id: str) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(SlaDefinitionTable)
                .filter(SlaDefinitionTable.tenant_id == tenant_id)
                .order_by(SlaDefinitionTable.created_at.desc())
                .all()
            )
            return [_sla_definition_record(r) for r in rows]

    # ------------------------------------------------------------------
    # Compliance evaluation
    # ------------------------------------------------------------------

    def evaluate_sla_compliance(self, request_id: str, tenant_id: str) -> dict:
        """Evaluate SLA compliance for a request.

        Checks elapsed time against all applicable SLA definitions and
        returns an overall status (green/yellow/red) plus a list of breaches.
        """
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            request_row = (
                session.query(RequestTable)
                .filter(
                    RequestTable.id == request_id,
                    RequestTable.tenant_id == tenant_id,
                )
                .first()
            )
            if not request_row:
                return {"request_id": request_id, "status": "unknown", "breaches": []}

            created_at = request_row.created_at
            elapsed_hours = (now - created_at).total_seconds() / 3600.0 if created_at else 0

            # Find applicable SLA definitions: global (scope_id IS NULL) or
            # scoped to the request type or owner team.
            sla_rows = (
                session.query(SlaDefinitionTable)
                .filter(
                    SlaDefinitionTable.tenant_id == tenant_id,
                    SlaDefinitionTable.status == "active",
                )
                .all()
            )

            applicable: list[SlaDefinitionTable] = []
            for sla in sla_rows:
                if sla.scope_id is None:
                    applicable.append(sla)
                elif sla.scope_type == "request_type" and sla.scope_id == request_row.request_type:
                    applicable.append(sla)
                elif sla.scope_type == "team" and sla.scope_id == request_row.owner_team_id:
                    applicable.append(sla)

            breaches: list[dict] = []
            overall_status = "green"

            for sla in applicable:
                # Check response SLA
                if sla.response_target_hours is not None:
                    threshold_pct = sla.warning_threshold_pct / 100.0
                    if elapsed_hours >= sla.response_target_hours:
                        breaches.append({
                            "sla_id": sla.id,
                            "sla_name": sla.name,
                            "breach_type": "response",
                            "target_hours": sla.response_target_hours,
                            "actual_hours": round(elapsed_hours, 2),
                        })
                        overall_status = "red"
                    elif elapsed_hours >= sla.response_target_hours * threshold_pct:
                        if overall_status != "red":
                            overall_status = "yellow"

                # Check resolution SLA
                if sla.resolution_target_hours is not None:
                    threshold_pct = sla.warning_threshold_pct / 100.0
                    if elapsed_hours >= sla.resolution_target_hours:
                        breaches.append({
                            "sla_id": sla.id,
                            "sla_name": sla.name,
                            "breach_type": "resolution",
                            "target_hours": sla.resolution_target_hours,
                            "actual_hours": round(elapsed_hours, 2),
                        })
                        overall_status = "red"
                    elif elapsed_hours >= sla.resolution_target_hours * threshold_pct:
                        if overall_status != "red":
                            overall_status = "yellow"

                # Check review SLA
                if sla.review_deadline_hours is not None:
                    threshold_pct = sla.warning_threshold_pct / 100.0
                    if elapsed_hours >= sla.review_deadline_hours:
                        breaches.append({
                            "sla_id": sla.id,
                            "sla_name": sla.name,
                            "breach_type": "review",
                            "target_hours": sla.review_deadline_hours,
                            "actual_hours": round(elapsed_hours, 2),
                        })
                        overall_status = "red"
                    elif elapsed_hours >= sla.review_deadline_hours * threshold_pct:
                        if overall_status != "red":
                            overall_status = "yellow"

            return {
                "request_id": request_id,
                "status": overall_status,
                "elapsed_hours": round(elapsed_hours, 2),
                "applicable_sla_count": len(applicable),
                "breaches": breaches,
            }

    # ------------------------------------------------------------------
    # Breach recording
    # ------------------------------------------------------------------

    def record_breach(
        self,
        sla_id: str,
        request_id: str,
        breach_type: str,
        target_hours: float,
        actual_hours: float,
        severity: str,
        tenant_id: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        breach_id = f"sb_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = SlaBreachAuditTable(
                id=breach_id,
                tenant_id=tenant_id,
                sla_definition_id=sla_id,
                request_id=request_id,
                breach_type=breach_type,
                target_hours=target_hours,
                actual_hours=actual_hours,
                severity=severity,
                remediation_action=None,
                breached_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="sla.breach_recorded",
                aggregate_type="sla_breach",
                aggregate_id=breach_id,
                actor="system",
                detail=f"SLA breach ({breach_type}) for request {request_id}: {actual_hours:.1f}h vs {target_hours:.1f}h target",
                request_id=request_id,
            )
            session.commit()
            session.refresh(row)
            return _breach_record(row)

    def list_breaches(
        self, tenant_id: str, request_id: str | None = None
    ) -> list[dict]:
        with SessionLocal() as session:
            q = session.query(SlaBreachAuditTable).filter(
                SlaBreachAuditTable.tenant_id == tenant_id,
            )
            if request_id:
                q = q.filter(SlaBreachAuditTable.request_id == request_id)
            rows = q.order_by(SlaBreachAuditTable.breached_at.desc()).all()
            return [_breach_record(r) for r in rows]


sla_enforcement_service = SlaEnforcementService()
