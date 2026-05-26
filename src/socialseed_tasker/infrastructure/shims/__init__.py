"""Adapter shims that implement application Port Protocols.

Each shim wraps an existing infrastructure adapter and exposes
the canonical Protocol interface defined in application.ports.
Use these shims when the original adapter cannot be modified to
inherit the Protocol directly.
"""

from __future__ import annotations

from typing import Any

from socialseed_tasker.application.ports import (
    EmbeddingPort,
    GitPort,
    GraphPort,
    LoggerPort,
    NodeRecord,
    ParserPort,
    QueryResult,
    StoragePort,
)

# ---------------------------------------------------------------------------
# GraphPort shim
# ---------------------------------------------------------------------------

class GraphShim:
    """Shim that wraps Neo4jDriver and Neo4jTaskRepository into GraphPort."""

    def __init__(self, driver: Any, repository: Any) -> None:
        self._driver = driver
        self._repo = repository

    def create_node(self, label: str, properties: dict[str, Any]) -> str:
        driver = self._driver.driver
        with driver.session(database=self._driver.database) as session:
            result = session.run(
                "CREATE (n:$label) SET n = $props RETURN elementId(n) AS id",
                label=label,
                props=properties,
            )
            record = result.single()
            return record["id"] if record else ""

    def get_node(self, node_id: str) -> NodeRecord | None:
        driver = self._driver.driver
        with driver.session(database=self._driver.database) as session:
            result = session.run(
                "MATCH (n) WHERE elementId(n) = $id RETURN n",
                id=node_id,
            )
            record = result.single()
            if record is None:
                return None
            n = record["n"]
            return NodeRecord(
                id=node_id,
                labels=list(n.labels),
                properties=dict(n),
            )

    def run_cypher(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        driver = self._driver.driver
        with driver.session(database=self._driver.database) as session:
            result = session.run(query, **(params or {}))
            records = [dict(r) for r in result]
            return QueryResult(records=records)

    def delete_node(self, node_id: str) -> None:
        driver = self._driver.driver
        with driver.session(database=self._driver.database) as session:
            session.run(
                "MATCH (n) WHERE elementId(n) = $id DELETE n",
                id=node_id,
            )


# ---------------------------------------------------------------------------
# ParserPort shim
# ---------------------------------------------------------------------------

class ParserShim:
    """Shim that wraps CodeGraphParser into ParserPort."""

    def __init__(self, parser: Any) -> None:
        self._parser = parser

    def parse_file(self, path: str) -> dict[str, Any]:
        return {"path": path, "type": "module", "body": []}

    def extract_symbols(self, ast: dict[str, Any]) -> list[dict[str, Any]]:
        if hasattr(self._parser, "extract_symbols"):
            return self._parser.extract_symbols(ast)  # type: ignore[return-value]
        symbols = ast.get("body", [])
        return [s for s in symbols if isinstance(s, dict)]

    def extract_imports(self, ast: dict[str, Any]) -> list[str]:
        if hasattr(self._parser, "extract_imports"):
            return self._parser.extract_imports(ast)  # type: ignore[return-value]
        return []


# ---------------------------------------------------------------------------
# GitPort shim
# ---------------------------------------------------------------------------

class GitShim:
    """Shim that wraps GitHubAdapter into GitPort."""

    def __init__(self, adapter: Any) -> None:
        self._adapter = adapter

    def list_changed_files(self, ref: str) -> list[str]:
        if hasattr(self._adapter, "list_changed_files"):
            return self._adapter.list_changed_files(ref)  # type: ignore[return-value]
        return []

    def read_file_at_ref(self, path: str, ref: str) -> str:
        if hasattr(self._adapter, "read_file_at_ref"):
            return self._adapter.read_file_at_ref(path, ref)  # type: ignore[return-value]
        return ""

    def current_branch(self) -> str:
        if hasattr(self._adapter, "current_branch"):
            return self._adapter.current_branch()  # type: ignore[return-value]
        import os
        return os.environ.get("GIT_BRANCH", "main")


# ---------------------------------------------------------------------------
# EmbeddingPort shim
# ---------------------------------------------------------------------------

class EmbeddingShim:
    """Shim that wraps EmbeddingService into EmbeddingPort."""

    def __init__(self, service: Any) -> None:
        self._service = service

    def embed_text(self, text: str) -> list[float]:
        result = self._service.generate(text)
        return result if result is not None else []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


# ---------------------------------------------------------------------------
# StoragePort shim
# ---------------------------------------------------------------------------

class StorageShim:
    """In-memory key-value store implementing StoragePort."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def put(self, key: str, value: bytes, ttl_seconds: int | None = None) -> None:
        self._store[key] = value

    def get(self, key: str) -> bytes | None:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


# ---------------------------------------------------------------------------
# LoggerPort shim
# ---------------------------------------------------------------------------

class LoggerShim:
    """Shim that wraps Python's logging.Logger into LoggerPort."""

    def __init__(self, logger: Any) -> None:
        self._logger = logger

    def info(self, message: str, **fields: Any) -> None:
        extra = " ".join(f"{k}={v}" for k, v in fields.items())
        self._logger.info("%s %s", message, extra)

    def debug(self, message: str, **fields: Any) -> None:
        extra = " ".join(f"{k}={v}" for k, v in fields.items())
        self._logger.debug("%s %s", message, extra)

    def warning(self, message: str, **fields: Any) -> None:
        extra = " ".join(f"{k}={v}" for k, v in fields.items())
        self._logger.warning("%s %s", message, extra)

    def error(self, message: str, **fields: Any) -> None:
        extra = " ".join(f"{k}={v}" for k, v in fields.items())
        self._logger.error("%s %s", message, extra)
