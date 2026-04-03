"""Billing service -- usage metering, quota management, and enforcement."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy import func

from app.db.models import UsageMeterTable, QuotaDefinitionTable
from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service


def _usage_meter_record(row: UsageMeterTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "meter_type": row.meter_type,
        "resource_id": row.resource_id,
        "quantity": row.quantity,
        "unit": row.unit,
        "cost_amount": row.cost_amount,
        "cost_currency": row.cost_currency,
        "attributed_to": row.attributed_to,
        "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
    }


def _quota_record(row: QuotaDefinitionTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "meter_type": row.meter_type,
        "limit_value": row.limit_value,
        "period": row.period,
        "enforcement": row.enforcement,
        "budget_amount": row.budget_amount,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _period_start(period: str) -> datetime:
    """Return the start of the current period window."""
    now = datetime.now(timezone.utc)
    if period == "daily":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "weekly":
        start = now - timedelta(days=now.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    # Default: monthly
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class BillingService:
    """Usage metering, quota enforcement, and cost tracking."""

    # ------------------------------------------------------------------
    # Usage metering
    # ------------------------------------------------------------------

    def record_usage(self, payload: dict, tenant_id: str) -> dict:
        """Record a usage meter event.

        ``payload`` should contain: meter_type, quantity (default 1),
        unit (default 'count'), resource_id (optional), cost_amount
        (optional), cost_currency (default 'USD'), attributed_to (optional).
        """
        now = datetime.now(timezone.utc)
        meter_id = f"um_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = UsageMeterTable(
                id=meter_id,
                tenant_id=tenant_id,
                meter_type=payload.get("meter_type", "generic"),
                resource_id=payload.get("resource_id"),
                quantity=payload.get("quantity", 1),
                unit=payload.get("unit", "count"),
                cost_amount=payload.get("cost_amount"),
                cost_currency=payload.get("cost_currency", "USD"),
                attributed_to=payload.get("attributed_to"),
                recorded_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="billing.usage_recorded",
                aggregate_type="usage_meter",
                aggregate_id=meter_id,
                actor=payload.get("attributed_to", "system"),
                detail=f"Usage recorded: {row.meter_type} x{row.quantity}",
            )
            session.commit()
            session.refresh(row)
            return _usage_meter_record(row)

    def get_usage_summary(
        self, tenant_id: str, meter_type: str, period: str = "monthly"
    ) -> dict:
        """Aggregate total quantity and total cost for a meter type in the current period."""
        window_start = _period_start(period)

        with SessionLocal() as session:
            result = (
                session.query(
                    func.coalesce(func.sum(UsageMeterTable.quantity), 0).label("total_quantity"),
                    func.coalesce(func.sum(UsageMeterTable.cost_amount), 0.0).label("total_cost"),
                )
                .filter(
                    UsageMeterTable.tenant_id == tenant_id,
                    UsageMeterTable.meter_type == meter_type,
                    UsageMeterTable.recorded_at >= window_start,
                )
                .one()
            )
            return {
                "tenant_id": tenant_id,
                "meter_type": meter_type,
                "period": period,
                "window_start": window_start.isoformat(),
                "total_quantity": int(result.total_quantity),
                "total_cost": float(result.total_cost),
            }

    # ------------------------------------------------------------------
    # Quota management
    # ------------------------------------------------------------------

    def create_quota(self, payload: dict, tenant_id: str) -> dict:
        """Create a quota definition."""
        now = datetime.now(timezone.utc)
        quota_id = f"qd_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = QuotaDefinitionTable(
                id=quota_id,
                tenant_id=tenant_id,
                name=payload.get("name", "Unnamed quota"),
                meter_type=payload.get("meter_type", "generic"),
                limit_value=payload.get("limit_value", 1000),
                period=payload.get("period", "monthly"),
                enforcement=payload.get("enforcement", "soft"),
                budget_amount=payload.get("budget_amount"),
                status="active",
                created_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="billing.quota_created",
                aggregate_type="quota_definition",
                aggregate_id=quota_id,
                actor="system",
                detail=f"Quota '{row.name}' created: {row.meter_type} limit={row.limit_value}/{row.period}",
            )
            session.commit()
            session.refresh(row)
            return _quota_record(row)

    def list_quotas(self, tenant_id: str) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(QuotaDefinitionTable)
                .filter(QuotaDefinitionTable.tenant_id == tenant_id)
                .order_by(QuotaDefinitionTable.created_at.desc())
                .all()
            )
            return [_quota_record(r) for r in rows]

    # ------------------------------------------------------------------
    # Quota checking / enforcement
    # ------------------------------------------------------------------

    def check_quota(self, tenant_id: str, meter_type: str) -> dict:
        """Check current usage against the applicable quota for a meter type.

        Returns a dict with current usage, limit, remaining, and exceeded flag.
        """
        with SessionLocal() as session:
            quota = (
                session.query(QuotaDefinitionTable)
                .filter(
                    QuotaDefinitionTable.tenant_id == tenant_id,
                    QuotaDefinitionTable.meter_type == meter_type,
                    QuotaDefinitionTable.status == "active",
                )
                .first()
            )

            if not quota:
                return {
                    "tenant_id": tenant_id,
                    "meter_type": meter_type,
                    "current_usage": 0,
                    "limit": None,
                    "remaining": None,
                    "exceeded": False,
                }

            window_start = _period_start(quota.period)
            total_qty = (
                session.query(func.coalesce(func.sum(UsageMeterTable.quantity), 0))
                .filter(
                    UsageMeterTable.tenant_id == tenant_id,
                    UsageMeterTable.meter_type == meter_type,
                    UsageMeterTable.recorded_at >= window_start,
                )
                .scalar()
            )
            current = int(total_qty)
            remaining = max(0, quota.limit_value - current)

            return {
                "tenant_id": tenant_id,
                "meter_type": meter_type,
                "current_usage": current,
                "limit": quota.limit_value,
                "remaining": remaining,
                "exceeded": current >= quota.limit_value,
            }

    def assert_within_quota(self, tenant_id: str, meter_type: str) -> None:
        """Raise ``ValueError`` if a hard quota for the given meter type is exceeded."""
        with SessionLocal() as session:
            quota = (
                session.query(QuotaDefinitionTable)
                .filter(
                    QuotaDefinitionTable.tenant_id == tenant_id,
                    QuotaDefinitionTable.meter_type == meter_type,
                    QuotaDefinitionTable.status == "active",
                    QuotaDefinitionTable.enforcement == "hard",
                )
                .first()
            )

            if not quota:
                return  # No hard quota defined; allow

            window_start = _period_start(quota.period)
            total_qty = (
                session.query(func.coalesce(func.sum(UsageMeterTable.quantity), 0))
                .filter(
                    UsageMeterTable.tenant_id == tenant_id,
                    UsageMeterTable.meter_type == meter_type,
                    UsageMeterTable.recorded_at >= window_start,
                )
                .scalar()
            )
            current = int(total_qty)

            if current >= quota.limit_value:
                raise ValueError(
                    f"Hard quota exceeded for {meter_type}: "
                    f"{current}/{quota.limit_value} ({quota.period})"
                )


billing_service = BillingService()
