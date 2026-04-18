"""View projection service -- board views, graph views, and roadmap projections."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, text

from app.db.models import (
    ViewDefinitionTable,
    RequestRelationshipTable,
    PlanningConstructTable,
    PlanningMembershipTable,
)
from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state


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
    _COMPLETED_STATUSES = {"completed", "closed", "promoted"}

    @staticmethod
    def _request_projection_record(request) -> dict:
        status = request.status.value if hasattr(request.status, "value") else str(request.status)
        priority = request.priority.value if hasattr(request.priority, "value") else str(request.priority)
        updated_at = request.updated_at.isoformat() if request.updated_at else None
        return {
            "id": request.id,
            "title": request.title,
            "status": status,
            "priority": priority,
            "owner_team_id": request.owner_team_id,
            "request_type": request.request_type,
            "updated_at": updated_at,
        }

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
            sql_request_ids = {
                row[0]
                for row in session.execute(
                    text("select id from requests where tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id},
                ).fetchall()
            }
            from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

            dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
            dynamo_request_ids = {
                item["id"]
                for item in dynamodb_adapter._scan_items()
                if item.get("record_type") == "request" and item.get("tenant_id") == tenant_id
            }
            request_ids = sql_request_ids | dynamo_request_ids
            requests = [get_request_state(request_id, tenant_id) for request_id in request_ids]
            records = [
                self._request_projection_record(request)
                for request in requests
                if request is not None and not request.is_archived
            ]

            if filters.get("status"):
                records = [record for record in records if record["status"] == filters["status"]]
            if filters.get("priority"):
                records = [record for record in records if record["priority"] == filters["priority"]]
            if filters.get("owner_team_id"):
                records = [record for record in records if record["owner_team_id"] == filters["owner_team_id"]]
            if filters.get("request_type"):
                records = [record for record in records if record["request_type"] == filters["request_type"]]
            records.sort(key=lambda record: record["updated_at"] or "", reverse=True)

            lanes: dict[str, list[dict]] = defaultdict(list)
            for record in records:
                lane_key = record.get(group_by) or "unassigned"
                lanes[lane_key].append(record)

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
            root = get_request_state(request_id, tenant_id)
            if not root:
                return {"nodes": [], "edges": []}

            nodes: dict[str, dict] = {}
            edges: list[dict] = []

            # Add root node
            nodes[root.id] = {
                "id": root.id,
                "title": root.title,
                "status": root.status.value if hasattr(root.status, "value") else str(root.status),
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
                    target = get_request_state(rel.target_request_id, tenant_id)
                    if target:
                        nodes[target.id] = {
                            "id": target.id,
                            "title": target.title,
                            "status": target.status.value if hasattr(target.status, "value") else str(target.status),
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
                    source = get_request_state(rel.source_request_id, tenant_id)
                    if source:
                        nodes[source.id] = {
                            "id": source.id,
                            "title": source.title,
                            "status": source.status.value if hasattr(source.status, "value") else str(source.status),
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
                completed_count = sum(
                    1
                    for request_id in member_request_ids
                    for request in [get_request_state(request_id, tenant_id)]
                    if request is not None
                    and (request.status.value if hasattr(request.status, "value") else str(request.status)) in self._COMPLETED_STATUSES
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
