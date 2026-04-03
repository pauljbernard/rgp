"""Deployment environment service -- manage deployment environment configurations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import DeploymentEnvironmentTable
from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service


def _environment_record(row: DeploymentEnvironmentTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "mode": row.mode,
        "isolation_level": row.isolation_level,
        "config": row.config,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class DeploymentEnvironmentService:
    """Manages deployment environment definitions and their configurations."""

    def create_environment(
        self,
        name: str,
        mode: str,
        isolation_level: str,
        config: dict,
        tenant_id: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        env_id = f"de_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = DeploymentEnvironmentTable(
                id=env_id,
                tenant_id=tenant_id,
                name=name,
                mode=mode,
                isolation_level=isolation_level,
                config=config,
                status="active",
                created_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="deployment.environment_created",
                aggregate_type="deployment_environment",
                aggregate_id=env_id,
                actor="system",
                detail=f"Deployment environment '{name}' created (mode={mode}, isolation={isolation_level})",
            )
            session.commit()
            session.refresh(row)
            return _environment_record(row)

    def list_environments(self, tenant_id: str) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(DeploymentEnvironmentTable)
                .filter(DeploymentEnvironmentTable.tenant_id == tenant_id)
                .order_by(DeploymentEnvironmentTable.created_at.desc())
                .all()
            )
            return [_environment_record(r) for r in rows]

    def get_environment(self, env_id: str) -> dict:
        with SessionLocal() as session:
            row = (
                session.query(DeploymentEnvironmentTable)
                .filter(DeploymentEnvironmentTable.id == env_id)
                .one()
            )
            return _environment_record(row)

    def update_environment(
        self, env_id: str, config: dict, tenant_id: str
    ) -> dict:
        """Update the configuration of a deployment environment.

        Merges the provided config dict into the existing config and
        records an audit event.
        """
        with SessionLocal() as session:
            row = (
                session.query(DeploymentEnvironmentTable)
                .filter(
                    DeploymentEnvironmentTable.id == env_id,
                    DeploymentEnvironmentTable.tenant_id == tenant_id,
                )
                .one()
            )

            # Merge new config into existing
            merged = dict(row.config or {})
            merged.update(config)
            row.config = merged

            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="deployment.environment_updated",
                aggregate_type="deployment_environment",
                aggregate_id=env_id,
                actor="system",
                detail=f"Deployment environment '{row.name}' config updated",
            )
            session.commit()
            session.refresh(row)
            return _environment_record(row)


deployment_environment_service = DeploymentEnvironmentService()
