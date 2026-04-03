"""Dependency execution service — pre-transition dependency checks.

Provides a lightweight facade over ``RelationshipGraphService`` to determine
whether a request can proceed to a target status given its dependency graph.
"""

from __future__ import annotations

from app.db.models import RequestRelationshipTable, RequestTable
from app.db.session import SessionLocal
from app.services.relationship_graph_service import relationship_graph_service

_TERMINAL_STATUSES = {"completed", "cancelled"}
_BLOCKING_TYPES = {"blocks", "depends_on"}


class DependencyExecutionService:
    """Pre-transition dependency validation."""

    def check_dependencies(
        self,
        request_id: str,
        target_status: str,
        tenant_id: str,
    ) -> list[str]:
        """Return a list of request IDs that block *request_id* from
        reaching *target_status*.

        Only ``blocks`` and ``depends_on`` relationship types are
        considered blocking.  A dependency is considered unmet if its
        source request has not reached a terminal status (``completed``
        or ``cancelled``).
        """
        with SessionLocal() as session:
            inbound = (
                session.query(RequestRelationshipTable)
                .filter(
                    RequestRelationshipTable.target_request_id == request_id,
                    RequestRelationshipTable.relationship_type.in_(_BLOCKING_TYPES),
                )
                .all()
            )

            blockers: list[str] = []
            for rel in inbound:
                source = (
                    session.query(RequestTable)
                    .filter(
                        RequestTable.id == rel.source_request_id,
                        RequestTable.tenant_id == tenant_id,
                    )
                    .first()
                )
                if source and source.status not in _TERMINAL_STATUSES:
                    blockers.append(source.id)

            return blockers

    def can_proceed(
        self,
        request_id: str,
        target_status: str,
        tenant_id: str,
    ) -> bool:
        """Return ``True`` if *request_id* has no blocking dependencies
        preventing transition to *target_status*."""
        return len(self.check_dependencies(request_id, target_status, tenant_id)) == 0


dependency_execution_service = DependencyExecutionService()
