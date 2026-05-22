"""In-memory fake GraphRepository for domain-level tests (no infrastructure)."""

from __future__ import annotations

from socialseed_tasker.application.dtos import DependencyEdge
from socialseed_tasker.application.repositories import GraphRepository


class FakeGraphRepository(GraphRepository):
    """In-memory dependency graph backed by an adjacency list.

    - add_dependency builds an adjacency dict: from_id -> [to_id, ...]
    - find_impact_set does a BFS in the reverse direction
      (who transitively depends on the given issue).
    """

    def __init__(self) -> None:
        self._edges: dict[str, list[str]] = {}

    def add_dependency(self, edge: DependencyEdge) -> None:
        self._edges.setdefault(edge.to_issue_id, [])
        self._edges.setdefault(edge.from_issue_id, [])
        self._edges[edge.from_issue_id].append(edge.to_issue_id)

    def get_dependencies(self, issue_id: str, depth: int = 1) -> list[DependencyEdge]:
        visited: set[str] = set()
        result: list[DependencyEdge] = []
        queue: list[tuple[str, int]] = [(issue_id, 0)]
        while queue:
            node, d = queue.pop(0)
            if d >= depth:
                continue
            for nxt in self._edges.get(node, []):
                if nxt not in visited:
                    visited.add(nxt)
                    result.append(DependencyEdge(from_issue_id=node, to_issue_id=nxt, relation="DEPENDS_ON"))
                    queue.append((nxt, d + 1))
        return result

    def find_impact_set(self, issue_id: str, max_depth: int = 5) -> list[str]:
        reverse: dict[str, list[str]] = {}
        for src, targets in self._edges.items():
            for t in targets:
                reverse.setdefault(t, []).append(src)

        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(issue_id, 0)]
        while queue:
            node, d = queue.pop(0)
            if d >= max_depth:
                continue
            for parent in reverse.get(node, []):
                if parent not in visited:
                    visited.add(parent)
                    queue.append((parent, d + 1))
        return list(visited)
