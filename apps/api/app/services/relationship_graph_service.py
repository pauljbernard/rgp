"""Relationship graph service — traversal, impact analysis, and dependency ordering.

Operates on the ``RequestRelationshipTable`` to provide graph algorithms
(BFS traversal, impact analysis, dependency validation, topological sort)
over the request relationship graph.
"""

from __future__ import annotations

from collections import defaultdict, deque

from app.db.models import RequestRelationshipTable, RequestTable
from app.db.session import SessionLocal


class RelationshipGraphService:
    """Graph operations over request relationships."""

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def traverse(
        self,
        request_id: str,
        direction: str = "outbound",
        max_depth: int = 5,
        tenant_id: str | None = None,
    ) -> list[dict]:
        """BFS traversal from *request_id* in the given direction.

        Args:
            request_id: Starting node.
            direction: ``"outbound"`` follows source->target edges,
                ``"inbound"`` follows target->source.
            max_depth: Maximum traversal depth.
            tenant_id: Optional tenant filter (applied to related
                request rows).

        Returns:
            List of relationship dicts with ``source``, ``target``,
            ``type``, and ``depth`` keys.
        """
        with SessionLocal() as session:
            visited: set[str] = set()
            queue: deque[tuple[str, int]] = deque()
            queue.append((request_id, 0))
            visited.add(request_id)
            results: list[dict] = []

            while queue:
                current_id, depth = queue.popleft()
                if depth >= max_depth:
                    continue

                if direction == "outbound":
                    edges = (
                        session.query(RequestRelationshipTable)
                        .filter(
                            RequestRelationshipTable.source_request_id == current_id
                        )
                        .all()
                    )
                    for edge in edges:
                        results.append(
                            {
                                "source": edge.source_request_id,
                                "target": edge.target_request_id,
                                "type": edge.relationship_type,
                                "depth": depth + 1,
                            }
                        )
                        if edge.target_request_id not in visited:
                            visited.add(edge.target_request_id)
                            queue.append((edge.target_request_id, depth + 1))
                else:
                    edges = (
                        session.query(RequestRelationshipTable)
                        .filter(
                            RequestRelationshipTable.target_request_id == current_id
                        )
                        .all()
                    )
                    for edge in edges:
                        results.append(
                            {
                                "source": edge.source_request_id,
                                "target": edge.target_request_id,
                                "type": edge.relationship_type,
                                "depth": depth + 1,
                            }
                        )
                        if edge.source_request_id not in visited:
                            visited.add(edge.source_request_id)
                            queue.append((edge.source_request_id, depth + 1))

            return results

    # ------------------------------------------------------------------
    # Impact analysis
    # ------------------------------------------------------------------

    def impact_analysis(self, request_id: str, tenant_id: str) -> list[str]:
        """Return all request IDs transitively affected by *request_id*.

        Follows outbound edges (dependencies that depend on this request).
        """
        edges = self.traverse(request_id, direction="outbound", max_depth=20, tenant_id=tenant_id)
        affected: set[str] = set()
        for edge in edges:
            affected.add(edge["target"])
        return sorted(affected)

    # ------------------------------------------------------------------
    # Dependency checks
    # ------------------------------------------------------------------

    def assert_dependencies_met(self, request_id: str, tenant_id: str) -> None:
        """Raise ``ValueError`` if any blocking inbound dependency is unmet.

        A dependency is considered *blocking* if its relationship type is
        ``"blocks"`` or ``"depends_on"`` and the source request is not in
        a terminal status (``completed``, ``cancelled``).
        """
        _TERMINAL = {"completed", "cancelled"}
        _BLOCKING_TYPES = {"blocks", "depends_on"}

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
                if source and source.status not in _TERMINAL:
                    blockers.append(source.id)

            if blockers:
                raise ValueError(
                    f"Blocking dependencies not met for {request_id}: "
                    f"{', '.join(blockers)}"
                )

    # ------------------------------------------------------------------
    # Topological sort
    # ------------------------------------------------------------------

    def get_dependency_order(
        self, request_ids: list[str], tenant_id: str
    ) -> list[str]:
        """Return a topological ordering of *request_ids* based on their
        dependency edges.

        Requests that have no dependencies appear first. Raises
        ``ValueError`` if a cycle is detected among the given ids.
        """
        id_set = set(request_ids)

        with SessionLocal() as session:
            edges = (
                session.query(RequestRelationshipTable)
                .filter(
                    RequestRelationshipTable.source_request_id.in_(id_set),
                    RequestRelationshipTable.target_request_id.in_(id_set),
                    RequestRelationshipTable.relationship_type.in_(
                        {"blocks", "depends_on"}
                    ),
                )
                .all()
            )

        # Build adjacency (source must complete before target).
        graph: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {rid: 0 for rid in request_ids}
        for edge in edges:
            graph[edge.source_request_id].append(edge.target_request_id)
            in_degree[edge.target_request_id] = in_degree.get(edge.target_request_id, 0) + 1

        queue: deque[str] = deque(
            rid for rid in request_ids if in_degree.get(rid, 0) == 0
        )
        ordered: list[str] = []

        while queue:
            node = queue.popleft()
            ordered.append(node)
            for neighbour in graph.get(node, []):
                in_degree[neighbour] -= 1
                if in_degree[neighbour] == 0:
                    queue.append(neighbour)

        if len(ordered) != len(request_ids):
            raise ValueError(
                "Cycle detected in dependency graph — topological sort impossible"
            )

        return ordered


relationship_graph_service = RelationshipGraphService()
