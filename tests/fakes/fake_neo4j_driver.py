"""Fake Neo4j driver for unit testing.

Provides an in-memory graph simulation that mimics the Neo4j driver interface.
Allows unit testing of repository code without requiring an actual Neo4j instance.
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
        """Get the single record from the result."""
        if self._records:
            return self._records[0]
        return None

    def single_or_none(self) -> dict[str, Any] | None:
        """Get the single record or None if no records."""
        return self.single()

    def consume(self) -> FakeSummary:
        """Consume the result and return a summary."""
        return FakeSummary()

    def __iter__(self):
        """Iterate over the records."""
        return iter(self._records)

    def __next__(self):
        """Get the next record."""
        if self._index < len(self._records):
            record = self._records[self._index]
            self._index += 1
            return record
        raise StopIteration


class FakeSummary:
    """Fake Neo4j Result Summary for unit testing."""

    def __init__(
        self,
        counters: dict[str, int] | None = None,
        type: str = "r",
        stats: dict[str, int] | None = None,
    ) -> None:
        self._counters = counters or {}
        self._type = type
        self._stats = stats or {}

    @property
    def counters(self) -> dict[str, int]:
        return self._counters


class FakeSession:
    """Fake Neo4j Session for unit testing."""

    def __init__(self, driver: FakeNeo4jDriver) -> None:
        self._driver = driver
        self._in_transaction = False

    @contextmanager
    def begin_transaction(self):
        """Begin a transaction."""
        self._in_transaction = True
        try:
            yield self
        finally:
            self._in_transaction = False

    def run(self, query: str, **params) -> FakeResult:
        """Execute a Cypher query and return results."""
        return self._driver._execute_query(query, params)

    def close(self) -> None:
        """Close the session."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class FakeNeo4jDriver:
    """In-memory Neo4j replacement for unit tests.

    Provides a simple in-memory graph simulation that mimics the Neo4j driver interface.
    Allows setting up test data and executing simple Cypher queries.
    """

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
        """Initialize the driver (no-op for fake)."""
        self._initialized = True

    def close(self) -> None:
        """Close the driver (no-op for fake)."""
        pass

    def health_check(self) -> bool:
        """Check driver health."""
        return True

    def verify_connectivity(self) -> bool:
        """Verify connectivity."""
        return True

    @contextmanager
    def session(self, database: str | None = None):
        """Get a session for executing queries."""
        yield FakeSession(self)

    def add_node(self, label: str, properties: dict[str, Any]) -> str:
        """Add a node to the in-memory graph.

        Args:
            label: The label for the node (e.g., "Issue", "Component")
            properties: The node properties

        Returns:
            The ID of the created node
        """
        node_id = properties.get("id", str(uuid4()))
        node = {"id": node_id, "_labels": [label], **properties}
        self._nodes[node_id] = node
        return node_id

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Add a relationship to the in-memory graph.

        Args:
            from_id: The ID of the start node
            to_id: The ID of the end node
            rel_type: The relationship type (e.g., "DEPENDS_ON")
            properties: Optional relationship properties
        """
        rel = {
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            **(properties or {}),
        }
        self._relationships.append(rel)

    def _execute_query(self, query: str, params: dict[str, Any]) -> FakeResult:
        """Execute a Cypher query and return results.

        Supports basic Cypher patterns:
        - MATCH (n:Label {id: $id}) RETURN n
        - MATCH (n:Label) RETURN n
        - CREATE (n:Label {props}) RETURN n
        - MERGE (n:Label {props}) RETURN n
        - MATCH (a)-[:REL]->(b) RETURN a, b
        """
        query_lower = query.lower().strip()

        if query_lower.startswith("match"):
            return self._execute_match(query, params)
        elif query_lower.startswith("create"):
            return self._execute_create(query, params)
        elif query_lower.startswith("merge"):
            return self._execute_merge(query, params)
        elif query_lower.startswith("return 1"):
            return FakeResult([{"ok": 1}], keys=["ok"])
        else:
            return FakeResult()

    def _execute_match(self, query: str, params: dict[str, Any]) -> FakeResult:
        """Execute a MATCH query."""
        records = []

        if "return 1" in query.lower():
            return FakeResult([{"ok": 1}], keys=["ok"])

        if "(n:issue)" in query.lower() or "(n:issue {" in query.lower():
            label = "Issue"
        elif "(n:component)" in query.lower() or "(n:component {" in query.lower():
            label = "Component"
        elif "(n:constraint)" in query.lower():
            label = "Constraint"
        else:
            label = None

        if label:
            for node_id, node in self._nodes.items():
                if node.get("_labels") and label in node["_labels"]:
                    if "where n.id = $" in query.lower() or "where n.id = '" in query.lower():
                        continue
                    records.append(node)
                elif "(n:issue)" in query.lower() or "(n:component)" in query.lower():
                    if node.get("_labels") and label in node["_labels"]:
                        records.append(node)

        if "optional match" in query.lower():
            if not records and params:
                for key in params:
                    if key in self._nodes:
                        records.append(self._nodes[key])

        if "(a)" in query.lower() and "(b)" in query.lower():
            if "()-[:depends_on]->()" in query.lower() or "(a)-[:depends_on]->(b)" in query.lower():
                for rel in self._relationships:
                    if rel.get("type") == "DEPENDS_ON":
                        from_node = self._nodes.get(rel.get("from", ""))
                        to_node = self._nodes.get(rel.get("to", ""))
                        if from_node and to_node:
                            records.append({"a": from_node, "b": to_node})

        return FakeResult(records)

    def _execute_create(self, query: str, params: dict[str, Any]) -> FakeResult:
        """Execute a CREATE query."""
        records = []

        if "(n:issue)" in query.lower():
            node_id = params.get("id", str(uuid4()))
            node = {
                "id": node_id,
                "_labels": ["Issue"],
                "title": params.get("title", ""),
                "description": params.get("description", ""),
                "status": params.get("status", "OPEN"),
                "priority": params.get("priority", "MEDIUM"),
                "component_id": params.get("component_id", ""),
                "labels": params.get("labels", []),
                "created_at": params.get("created_at") or datetime.now(timezone.utc),
                "updated_at": params.get("updated_at") or datetime.now(timezone.utc),
            }
            self._nodes[node_id] = node
            records.append(node)
        elif "(n:component)" in query.lower():
            node_id = params.get("id", str(uuid4()))
            node = {
                "id": node_id,
                "_labels": ["Component"],
                "name": params.get("name", ""),
                "project": params.get("project", ""),
                "description": params.get("description", ""),
                "created_at": params.get("created_at") or datetime.now(timezone.utc),
                "updated_at": params.get("updated_at") or datetime.now(timezone.utc),
            }
            self._nodes[node_id] = node
            records.append(node)

        return FakeResult(records)

    def _execute_merge(self, query: str, params: dict[str, Any]) -> FakeResult:
        """Execute a MERGE query (same as CREATE for now)."""
        return self._execute_create(query, params)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_nodes_by_label(self, label: str) -> list[dict[str, Any]]:
        """Get all nodes with a specific label."""
        return [
            node for node in self._nodes.values() if label in node.get("_labels", [])
        ]

    def clear(self) -> None:
        """Clear all nodes and relationships."""
        self._nodes.clear()
        self._relationships.clear()
        self._constraints.clear()

    def setup_issue(
        self,
        issue_id: str,
        title: str,
        component_id: str,
        status: str = "OPEN",
        priority: str = "MEDIUM",
        description: str = "",
        labels: list[str] | None = None,
    ) -> None:
        """Helper to set up an issue node."""
        node = {
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
        self._nodes[issue_id] = node

    def setup_component(
        self,
        component_id: str,
        name: str,
        project: str,
        description: str = "",
    ) -> None:
        """Helper to set up a component node."""
        node = {
            "id": component_id,
            "_labels": ["Component"],
            "name": name,
            "project": project,
            "description": description,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self._nodes[component_id] = node

    def add_dependency(self, from_issue_id: str, to_issue_id: str) -> None:
        """Add a DEPENDS_ON relationship between issues."""
        self.add_relationship(from_issue_id, to_issue_id, "DEPENDS_ON")
        if from_issue_id in self._nodes:
            issue = self._nodes[from_issue_id]
            deps = issue.get("dependencies", [])
            if to_issue_id not in deps:
                deps.append(to_issue_id)
                issue["dependencies"] = deps