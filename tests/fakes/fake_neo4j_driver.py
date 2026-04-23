"""Fake Neo4j driver for unit testing.

Provides an in-memory graph simulation that mimics the Neo4j driver interface.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class FakeResult:
    """Fake Neo4j Result for unit testing."""

    def __init__(self, records: list[dict[str, Any]] | None = None, keys: list[str] | None = None) -> None:
        self._records = records or []
        self._keys = keys or []
        self._index = 0

    def single(self) -> dict[str, Any] | None:
        if self._records:
            return self._records[0]
        return None

    def single_or_none(self) -> dict[str, Any] | None:
        return self.single()

    def consume(self) -> FakeSummary:
        return FakeSummary()

    def __iter__(self):
        return iter(self._records)

    def __next__(self):
        if self._index < len(self._records):
            record = self._records[self._index]
            self._index += 1
            return record
        raise StopIteration


class FakeSummary:
    def __init__(self, counters: dict[str, int] | None = None, type: str = "r", stats: dict[str, int] | None = None) -> None:
        self._counters = counters or {}
        self._type = type
        self._stats = stats or {}

    @property
    def counters(self) -> dict[str, int]:
        return self._counters


class FakeSession:
    def __init__(self, driver: FakeNeo4jDriver) -> None:
        self._driver = driver
        self._in_transaction = False

    @contextmanager
    def begin_transaction(self):
        self._in_transaction = True
        try:
            yield self
        finally:
            self._in_transaction = False

    def run(self, query: str, **params) -> FakeResult:
        return self._driver._execute_query(query, params)

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class FakeNeo4jDriver:
    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._relationships: list[dict[str, Any]] = []
        self._constraints: dict[str, set[str]] = {}
        self._initialized = True
        self._inner_driver = self

    @property
    def driver(self) -> FakeNeo4jDriver:
        return self._inner_driver

    @property
    def database(self) -> str:
        return "neo4j"

    @property
    def uri(self) -> str:
        return "bolt://fake:7687"

    def connect(self) -> None:
        self._initialized = True

    def close(self) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def verify_connectivity(self) -> bool:
        return True

    @contextmanager
    def session(self, database: str | None = None):
        yield FakeSession(self)

    def add_node(self, label: str, properties: dict[str, Any]) -> str:
        node_id = properties.get("id", str(uuid4()))
        node = {"id": node_id, "_labels": [label], **properties}
        self._nodes[node_id] = node
        return node_id

    def add_relationship(self, from_id: str, to_id: str, rel_type: str, properties: dict[str, Any] | None = None) -> None:
        rel = {"from": from_id, "to": to_id, "type": rel_type, **(properties or {})}
        self._relationships.append(rel)

    def _execute_query(self, query: str, params: dict[str, Any]) -> FakeResult:
        q = query.lower().strip()
        if q.startswith("match"):
            return self._execute_match(query, params)
        elif q.startswith("create") or q.startswith("merge"):
            return self._execute_create(query, params)
        elif q.startswith("return 1"):
            return FakeResult([{"ok": 1}], keys=["ok"])
        else:
            return FakeResult()

    def _execute_match(self, query: str, params: dict[str, Any]) -> FakeResult:
        q = query.lower()

        # GET_ISSUE
        if "i:issue" in q and "id: $id" in q:
            node = self._nodes.get(params.get("id"))
            if node and "Issue" in node.get("_labels", []):
                return FakeResult([{"i": node}])
            return FakeResult()
        
        # GET_COMPONENT
        if "c:component" in q and "id: $id" in q:
            node = self._nodes.get(params.get("id"))
            if node and "Component" in node.get("_labels", []):
                return FakeResult([{"c": node}])
            return FakeResult()

        # LIST_ISSUES
        if "optional match" in q and "with i" in q:
            comp_id = params.get("component_id")
            status_filter = params.get("status")
            project_filter = params.get("project")
            results = []
            for node in self._nodes.values():
                if "Issue" not in node.get("_labels", []):
                    continue
                if comp_id is not None and node.get("component_id") != comp_id:
                    continue
                if status_filter is not None and node.get("status") != status_filter:
                    continue
                node_id = node["id"]
                dep_ids = [r["to"] for r in self._relationships if r.get("type") == "DEPENDS_ON" and r.get("from") == node_id]
                blocked_ids_list = [r["from"] for r in self._relationships if r.get("type") == "DEPENDS_ON" and r.get("to") == node_id]
                results.append({"i": node, "dep_ids": dep_ids, "blocked_ids": blocked_ids_list})
            return FakeResult(results)
        
        # LIST_COMPONENTS
        if "(c:component)" in q and "order by c.name" in q:
            project_filter = params.get("project")
            results = []
            for node in self._nodes.values():
                if "Component" not in node.get("_labels", []):
                    continue
                if project_filter is not None and node.get("project") != project_filter:
                    continue
                results.append({"c": node})
            return FakeResult(results)

        # GET_DEPENDENCIES
        if "depends_on" in q and "target:issue" in q and "id: $issue_id" in q and "<-" not in q:
            issue_id = str(params.get("issue_id", ""))
            results = [{"target": self._nodes[r["to"]]} for r in self._relationships if r.get("type") == "DEPENDS_ON" and r.get("from") == issue_id and r["to"] in self._nodes]
            return FakeResult(results)

        # GET_BLOCKED_ISSUES
        if "depends_on" in q and "distinct i" in q and "blocked_ids" not in q:
            blocked_ids = set()
            for rel in self._relationships:
                if rel.get("type") == "DEPENDS_ON":
                    from_node = self._nodes.get(rel.get("from", ""))
                    to_node = self._nodes.get(rel.get("to", ""))
                    if from_node and to_node and from_node.get("status") == "OPEN" and to_node.get("status") == "OPEN":
                        blocked_ids.add(rel["from"])
            return FakeResult([{"i": self._nodes[nid]} for nid in blocked_ids if nid in self._nodes])

        # GET_COMPONENT_BY_NAME
        if "{name: $name}" in q and "c:component" in q:
            name = params.get("name")
            project = params.get("project")
            for node in self._nodes.values():
                if "Component" in node.get("_labels", []) and node.get("name") == name:
                    if project is None or node.get("project") == project:
                        return FakeResult([{"c": node}])
            return FakeResult()

        return FakeResult()

    def _execute_create(self, query: str, params: dict[str, Any]) -> FakeResult:
        # Simplistic create for tests
        return FakeResult()

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        return self._nodes.get(node_id)

    def get_nodes_by_label(self, label: str) -> list[dict[str, Any]]:
        return [node for node in self._nodes.values() if label in node.get("_labels", [])]

    def clear(self) -> None:
        self._nodes.clear()
        self._relationships.clear()
        self._constraints.clear()

    def setup_issue(self, issue_id: str, title: str, component_id: str, status: str = "OPEN", priority: str = "MEDIUM", description: str = "", labels: list[str] | None = None) -> None:
        self._nodes[issue_id] = {
            "id": issue_id,
            "_labels": ["Issue"],
            "title": title,
            "component_id": component_id,
            "status": status,
            "priority": priority,
            "description": description,
            "labels": labels or [],
            "dependencies": [],
            "blocks": [],
            "affects": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "closed_at": None,
            "architectural_constraints": [],
            "agent_working": False,
            "manifest_todo": [],
            "manifest_files": [],
            "manifest_notes": [],
        }

    def setup_component(self, component_id: str, name: str, project: str, description: str = "") -> None:
        self._nodes[component_id] = {
            "id": component_id,
            "_labels": ["Component"],
            "name": name,
            "project": project,
            "description": description,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    def add_dependency(self, from_issue_id: str, to_issue_id: str) -> None:
        self.add_relationship(from_issue_id, to_issue_id, "DEPENDS_ON")