"""Neo4j-backed implementation of GraphRepository.

Note: Neo4j 5.x does not support MAP values as relationship properties.
Metadata dicts are serialized to JSON strings for storage and
parsed back to dicts on read.
"""

from __future__ import annotations

import json

from socialseed_tasker.application.dtos import DependencyEdge
from socialseed_tasker.application.exceptions import GraphPortError
from socialseed_tasker.application.ports import GraphPort
from socialseed_tasker.application.repositories import GraphRepository


class Neo4jGraphRepository(GraphRepository):
    """Neo4j-backed implementation of GraphRepository.

    Implementation notes:
    - Dependency edges are represented as relationships :DEPENDS_ON between Issue nodes.
    - get_dependencies returns edges with relation 'DEPENDS_ON' and metadata if present.
    - find_impact_set returns list of issue ids reachable via incoming DEPENDS_ON edges.
    - Metadata dicts are stored as JSON strings (Neo4j 5.x compat).
    """

    def __init__(self, graph: GraphPort) -> None:
        self._graph = graph

    def add_dependency(self, edge: DependencyEdge) -> None:
        try:
            cypher = (
                "MATCH (a:Issue {id: $from_id}), (b:Issue {id: $to_id}) "
                "MERGE (a)-[r:DEPENDS_ON]->(b) "
                "SET r.relation = $relation, r.metadata = $metadata"
            )
            self._graph.run_cypher(
                cypher,
                {
                    "from_id": edge.from_issue_id,
                    "to_id": edge.to_issue_id,
                    "relation": edge.relation,
                    "metadata": json.dumps(dict(edge.metadata or {})),
                },
            )
        except Exception as exc:
            raise GraphPortError(f"Failed to add dependency {edge}: {exc}") from exc

    def get_dependencies(self, issue_id: str, depth: int = 1) -> list[DependencyEdge]:
        try:
            cypher = (
                f"MATCH (a:Issue {{id: $id}})-[r:DEPENDS_ON*1..{depth}]->(b:Issue) "
                "UNWIND r AS rel "
                "RETURN a.id AS from_id, b.id AS to_id, rel.relation AS relation, rel.metadata AS metadata"
            )
            res = self._graph.run_cypher(cypher, {"id": issue_id})
            results = []
            for r in res.records:
                raw = r.get("metadata") or "{}"
                metadata = json.loads(raw) if isinstance(raw, str) else raw
                results.append(
                    DependencyEdge(
                        from_issue_id=str(r.get("from_id")),
                        to_issue_id=str(r.get("to_id")),
                        relation=str(r.get("relation") or "DEPENDS_ON"),
                        metadata=metadata,
                    )
                )
            return results
        except Exception as exc:
            raise GraphPortError(f"Failed to get dependencies for {issue_id}: {exc}") from exc

    def find_impact_set(self, issue_id: str, max_depth: int = 5) -> list[str]:
        try:
            cypher = (
                f"MATCH (target:Issue {{id: $id}}) "
                f"MATCH (dependent:Issue)-[:DEPENDS_ON*1..{max_depth}]->(target) "
                f"RETURN DISTINCT dependent.id AS id"
            )
            res = self._graph.run_cypher(cypher, {"id": issue_id})
            return [str(r.get("id")) for r in res.records]
        except Exception as exc:
            raise GraphPortError(f"Failed to compute impact set for {issue_id}: {exc}") from exc
