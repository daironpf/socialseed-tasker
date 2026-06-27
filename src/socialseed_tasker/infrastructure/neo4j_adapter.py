"""Concrete GraphPort implementation using the official Neo4j driver.

This adapter fully implements the GraphPort Protocol defined in
application/ports.py. It provides retry logic, error mapping, and
driver lifecycle management.
"""

from __future__ import annotations

import contextlib
import os
import time
from typing import Any

from neo4j.exceptions import Neo4jError, ServiceUnavailable

from neo4j import GraphDatabase, basic_auth
from socialseed_tasker.application.exceptions import GraphPortError
from socialseed_tasker.application.ports import GraphPort, NodeRecord, QueryResult
from socialseed_tasker.observability.logging import get_logger
from socialseed_tasker.observability.metrics import observe_operation

DEFAULT_NEO4J_URI = os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687")
DEFAULT_NEO4J_USER = os.getenv("TASKER_NEO4J_USER", "neo4j")
DEFAULT_NEO4J_PASSWORD = os.getenv("TASKER_NEO4J_PASSWORD", "neoSocial")
DEFAULT_MAX_RETRIES = int(os.getenv("TASKER_NEO4J_MAX_RETRIES", "3"))
DEFAULT_RETRY_BACKOFF = float(os.getenv("TASKER_NEO4J_RETRY_BACKOFF", "0.5"))


class Neo4jGraphAdapter(GraphPort):
    """Concrete GraphPort implementation using the official neo4j driver.

    Behavior guarantees
    - create_node returns a stable string id (elementId).
    - run_cypher returns QueryResult with records as list[Mapping[str, Any]].
    - Transient errors raise GraphPortError.
    - All Neo4j exceptions are wrapped as GraphPortError.
    """

    def __init__(
        self,
        uri: str = DEFAULT_NEO4J_URI,
        user: str = DEFAULT_NEO4J_USER,
        password: str = DEFAULT_NEO4J_PASSWORD,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._driver = GraphDatabase.driver(self._uri, auth=basic_auth(self._user, self._password))

    logger = get_logger("tasker.neo4j")

    def _with_retry(self, fn, *args, **kwargs):
        last_exc = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except (ServiceUnavailable, Neo4jError) as exc:
                last_exc = exc
                if attempt == self._max_retries:
                    raise GraphPortError(f"Neo4j operation failed after {attempt} attempts: {exc}") from exc
                time.sleep(self._retry_backoff * attempt)
        raise GraphPortError("Neo4j operation failed") from last_exc

    def create_node(self, label: str, properties: dict[str, Any]) -> str:
        """Create a node with label and properties. Return elementId as string."""
        with observe_operation("neo4j", "create_node"):
            self.logger.info("neo4j.create_node.start", extra={"label": label})

            def _op():
                with self._driver.session() as session:
                    result = session.run(
                        f"CREATE (n:{label}) SET n += $props RETURN elementId(n) AS id",
                        props=properties,
                    )
                    rec = result.single()
                    if rec is None:
                        raise GraphPortError("Failed to create node")
                    return str(rec["id"])

            result = self._with_retry(_op)
            self.logger.info("neo4j.create_node.end", extra={"node_id": result})
            return result

    def get_node(self, node_id: str) -> NodeRecord | None:
        """Return NodeRecord or None if not found."""
        with observe_operation("neo4j", "get_node"):
            self.logger.info("neo4j.get_node.start", extra={"node_id": node_id})

            def _op():
                with self._driver.session() as session:
                    result = session.run(
                        "MATCH (n) WHERE elementId(n) = $id RETURN labels(n) AS labels, properties(n) AS props",
                        id=node_id,
                    )
                    rec = result.single()
                    if rec is None:
                        return None
                    return NodeRecord(id=node_id, labels=list(rec["labels"]), properties=dict(rec["props"]))

            return self._with_retry(_op)

    def run_cypher(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        """Execute a read or write Cypher query and return structured results."""
        with observe_operation("neo4j", "run_cypher"):
            self.logger.info("neo4j.run_cypher.start")

            def _op():
                with self._driver.session() as session:
                    result = session.run(query, params or {})
                    records = [{k: v for k, v in r.items()} for r in result]
                    return QueryResult(records=records)

            return self._with_retry(_op)

    def delete_node(self, node_id: str) -> None:
        """Delete node by id. No-op if node does not exist."""
        with observe_operation("neo4j", "delete_node"):
            self.logger.info("neo4j.delete_node.start", extra={"node_id": node_id})

            def _op():
                with self._driver.session() as session:
                    session.run("MATCH (n) WHERE elementId(n) = $id DETACH DELETE n", id=node_id)
                    return None

            return self._with_retry(_op)

    def close(self) -> None:
        """Release Neo4j driver resources."""
        with contextlib.suppress(Exception):
            self._driver.close()
