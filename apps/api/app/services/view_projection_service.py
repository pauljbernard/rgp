"""View projection service -- board views, graph views, and roadmap projections."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func

from app.db.models import (
    ViewDefinitionTable,
    RequestTable,
    RequestRelationshipTable,
    PlanningConstructTable,
    PlanningMembershipTable,
)
from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service


def _view_definition_record(row: ViewDefinitionTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "view_type": row.view_type,
        "config": row.config,
        "status": row.status,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class ViewProjectionService:
    """Projects request data into board, graph, and roadmap views."""

    # ------------------------------------------------------------------
    # View definitions
    # ------------------------------------------------------------------

    def create_view_definition(
        self, payload: dict, actor_id: str, tenant_id: str
    ) -> dict:
        now = datetime.now(timezone.utc)
        view_id = f"vd_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = ViewDefinitionTable(
                id=view_id,
                tenant_id=tenant_id,
                name=payload.get("name", "Unnamed view"),
                view_type=payload.get("view_type", "board"),
                config=payload.get("config", {}),
                status="active",
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="view.definition_created",
                aggregate_type="view_definition",
                aggregate_id=view_id,
                actor=actor_id,
                detail=f"View definition '{row.name}' ({row.view_type}) created",
            )
            session.commit()
            session.refresh(row)
            return _view_definition_record(row)

    def list_view_definitions(
        self, tenant_id: str, view_type: str | None = None
    ) -> list[dict]:
        with SessionLocal() as session:
            q = session.query(ViewDefinitionTable).filter(
                ViewDefinitionTable.tenant_id == tenant_id,
            )
            if view_type:
                q = q.filter(ViewDefinitionTable.view_type == view_type)
            rows = q.order_by(ViewDefinitionTable.created_at.desc()).all()
            return [_view_definition_record(r) for r in rows]

    # ------------------------------------------------------------------
    # Board view projection
    # ------------------------------------------------------------------

    def project_board_view(
        self,
        tenant_id: str,
        group_by: str = "status",
        filters: dict | None = None,
    ) -> dict:
        """Group requests into swim lanes based on the group_by field.

        Supported group_by values: 'status', 'priority', 'owner_team_id'.
        Optional filters: status, priority, owner_team_id, request_type.

        Returns a dict of {lane_key: [request dicts]}.
        """
        filters = filters or {}

        with SessionLocal() as session:
            q = session.query(RequestTable).filter(
                RequestTable.tenant_id == tenant_id,
                RequestTable.is_archived.is_(False),
            )

            if filters.get("status"):
                q = q.filter(RequestTable.status == filters["status"])
            if filters.get("priority"):
                q = q.filter(RequestTable.priority == filters["priority"])
            if filters.get("owner_team_id"):
                q = q.filter(RequestTable.owner_team_id == filters["owner_team_id"])
            if filters.get("request_type"):
                q = q.filter(RequestTable.request_type == filters["request_type"])

            rows = q.order_by(RequestTable.updated_at.desc()).all()

            lanes: dict[str, list[dict]] = defaultdict(list)
            for r in rows:
                lane_key = getattr(r, group_by, "unknown") or "unassigned"
                lanes[lane_key].append({
                    "id": r.id,
                    "title": r.title,
                    "status": r.status,
                    "priority": r.priority,
                    "owner_team_id": r.owner_team_id,
                    "request_type": r.request_type,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                })

            return {
                "group_by": group_by,
                "lane_count": len(lanes),
                "total_requests": sum(len(v) for v in lanes.values()),
                "lanes": dict(lanes),
            }

    # ------------------------------------------------------------------
    # Graph view projection
    # ------------------------------------------------------------------

    def project_graph_view(self, request_id: str, tenant_id: str) -> dict:
        """Render a relationship graph as nodes and edges for a given request.

        Traverses one level of outbound and inbound relationships and
        includes the request itself as the root node.
        """
        with SessionLocal() as session:
            root = (
                session.query(RequestTable)
                .filter(
                    RequestTable.id == request_id,
                    RequestTable.tenant_id == tenant_id,
                )
                .first()
            )
            if not root:
                return {"nodes": [], "edges": []}

            nodes: dict[str, dict] = {}
            edges: list[dict] = []

            # Add root node
            nodes[root.id] = {
                "id": root.id,
                "title": root.title,
                "status": root.status,
                "type": "root",
            }

            # Outbound relationships
            outbound = (
                session.query(RequestRelationshipTable)
                .filter(RequestRelationshipTable.source_request_id == request_id)
                .all()
            )
            for rel in outbound:
                edges.append({
                    "source": rel.source_request_id,
                    "target": rel.target_request_id,
                    "type": rel.relationship_type,
                })
                if rel.target_request_id not in nodes:
                    target = (
                        session.query(RequestTable)
                        .filter(RequestTable.id == rel.target_request_id)
                        .first()
                    )
                    if target:
                        nodes[target.id] = {
                            "id": target.id,
                            "title": target.title,
                            "status": target.status,
                            "type": "related",
                        }

            # Inbound relationships
            inbound = (
                session.query(RequestRelationshipTable)
                .filter(RequestRelationshipTable.target_request_id == request_id)
                .all()
            )
            for rel in inbound:
                edges.append({
                    "source": rel.source_request_id,
                    "target": rel.target_request_id,
                    "type": rel.relationship_type,
                })
                if rel.source_request_id not in nodes:
                    source = (
                        session.query(RequestTable)
                        .filter(RequestTable.id == rel.source_request_id)
                        .first()
                    )
                    if source:
                        nodes[source.id] = {
                            "id": source.id,
                            "title": source.title,
                            "status": source.status,
                            "type": "related",
                        }

            return {
                "root_id": request_id,
                "nodes": list(nodes.values()),
                "edges": edges,
            }

    # ------------------------------------------------------------------
    # Roadmap view projection
    # ------------------------------------------------------------------

    def project_roadmap_view(
        self, tenant_id: str, construct_type: str | None = None
    ) -> dict:
        """Render planning constructs as a timeline with member counts and status.

        Optionally filter by construct type (initiative, program, release, etc.).
        """
        with SessionLocal() as session:
            q = session.query(PlanningConstructTable).filter(
                PlanningConstructTable.tenant_id == tenant_id,
            )
            if construct_type:
                q = q.filter(PlanningConstructTable.type == construct_type)

            constructs = q.order_by(
                PlanningConstructTable.target_date.asc().nulls_last(),
                PlanningConstructTable.priority.desc(),
            ).all()

            items: list[dict] = []
            for c in constructs:
                member_count = (
                    session.query(func.count(PlanningMembershipTable.id))
                    .filter(PlanningMembershipTable.planning_construct_id == c.id)
                    .scalar()
                )

                # Count completed members
                member_request_ids = [
                    m.request_id
                    for m in session.query(PlanningMembershipTable)
                    .filter(PlanningMembershipTable.planning_construct_id == c.id)
                    .all()
                ]
                completed_count = 0
                if member_request_ids:
                    completed_count = (
                        session.query(func.count(RequestTable.id))
                        .filter(
                            RequestTable.id.in_(member_request_ids),
                            RequestTable.status.in_(["completed", "closed"]),
                        )
                        .scalar()
                    )

                completion_pct = (
                    round(completed_count / member_count * 100.0, 1)
                    if member_count > 0
                    else 0.0
                )

                items.append({
                    "id": c.id,
                    "type": c.type,
                    "name": c.name,
                    "status": c.status,
                    "priority": c.priority,
                    "target_date": c.target_date.isoformat() if c.target_date else None,
                    "capacity_budget": c.capacity_budget,
                    "owner_team_id": c.owner_team_id,
                    "member_count": member_count,
                    "completed_count": completed_count,
                    "completion_pct": completion_pct,
                })

            return {
                "construct_type": construct_type,
                "total_constructs": len(items),
                "items": items,
            }


view_projection_service = ViewProjectionService()
