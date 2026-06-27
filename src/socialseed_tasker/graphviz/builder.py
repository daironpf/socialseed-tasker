from __future__ import annotations

from collections import deque
from typing import Any

from socialseed_tasker.application.dtos import IssueSummary


class Graph:
    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[tuple[str, str, str]] = []

    def add_node(self, node_id: str, label: str):
        self.nodes[node_id] = {"id": node_id, "label": label}

    def add_edge(self, from_id: str, to_id: str, relation: str = "DEPENDS_ON"):
        self.edges.append((from_id, to_id, relation))

    def to_json(self) -> dict[str, Any]:
        nodes = [self.nodes[k] for k in sorted(self.nodes.keys())]
        edges = sorted(
            [{"from": f, "to": t, "relation": r} for (f, t, r) in self.edges],
            key=lambda e: (e["from"], e["to"]),
        )
        return {"nodes": nodes, "edges": edges}


def build_graph(container) -> Graph:
    g = Graph()
    issues: list[IssueSummary] = list(container.issue_repo.list())
    issues_sorted = sorted(issues, key=lambda i: str(i.id))
    for i in issues_sorted:
        g.add_node(str(i.id), i.title or str(i.id))
    try:
        result = container.graph._graph.run_cypher(
            "MATCH (a:Issue)-[r:DEPENDS_ON]->(b:Issue) "
            "RETURN a.id AS from_id, b.id AS to_id, r.relation AS relation "
            "ORDER BY from_id, to_id"
        )
        for record in result.records:
            f = str(record.get("from_id"))
            t = str(record.get("to_id"))
            rel = str(record.get("relation", "DEPENDS_ON"))
            if f not in g.nodes:
                g.add_node(f, f)
            if t not in g.nodes:
                g.add_node(t, t)
            g.add_edge(f, t, rel)
    except Exception:
        edges_data: list[dict] = []
        if hasattr(container.graph_repo, "list_edges"):
            edges_data = list(container.graph_repo.list_edges())
        edges_sorted = sorted(edges_data, key=lambda e: (str(e.get("from")), str(e.get("to"))))
        for e in edges_sorted:
            f = str(e.get("from"))
            t = str(e.get("to"))
            rel = e.get("relation", "DEPENDS_ON")
            if f not in g.nodes:
                g.add_node(f, f)
            if t not in g.nodes:
                g.add_node(t, t)
            g.add_edge(f, t, rel)
    return g


def compute_impact(graph: Graph, node_id: str, max_depth: int = 5) -> list[str]:
    visited = set()
    q: deque = deque()
    q.append((node_id, 0))
    result: list[str] = []
    adj: dict[str, list[str]] = {}
    for e in sorted(graph.edges, key=lambda x: (x[0], x[1])):
        adj.setdefault(e[0], []).append(e[1])
    while q:
        cur, depth = q.popleft()
        if depth >= max_depth:
            continue
        for nb in adj.get(cur, []):
            if nb not in visited and nb != node_id:
                visited.add(nb)
                result.append(nb)
                q.append((nb, depth + 1))
    return result
