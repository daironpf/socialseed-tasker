"""Application ports (Protocol interfaces) for external adapters.

Every infrastructure adapter MUST implement the corresponding Protocol
defined here. This module is the canonical contract that removes ambiguity
for autonomous agents: adapters must implement these exact methods and
signatures so the agent can wire dependencies without guessing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class NodeRecord:
    id: str
    labels: list[str]
    properties: dict[str, Any]


@dataclass
class QueryResult:
    records: list[Mapping[str, Any]]


@runtime_checkable
class GraphPort(Protocol):
    """Minimal graph database contract used by application use cases.

    Implementations must:
    - Use stable string node ids for create_node return values.
    - Raise GraphPortError on transient failures.
    - Not mutate input dicts.
    """

    def create_node(self, label: str, properties: dict[str, Any]) -> str:
        """Create a node with label and properties. Return node id as string."""

    def get_node(self, node_id: str) -> NodeRecord | None:
        """Return NodeRecord or None if not found."""

    def run_cypher(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        """Execute a read or write Cypher query and return structured results."""

    def delete_node(self, node_id: str) -> None:
        """Delete node by id. No-op if node does not exist."""


@runtime_checkable
class ParserPort(Protocol):
    """Code parser contract.

    Implementations must:
    - Return deterministic AST-like structures for the same input.
    - Not raise on parseable files; raise ParserError on unreadable files.
    """

    def parse_file(self, path: str) -> dict[str, Any]:
        """Parse a source file and return an AST-like dict."""

    def extract_symbols(self, ast: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a list of symbol descriptors extracted from AST."""

    def extract_imports(self, ast: dict[str, Any]) -> list[str]:
        """Return a list of import targets (module paths or file paths)."""


@runtime_checkable
class GitPort(Protocol):
    """Git operations contract.

    Implementations must be read-only unless explicitly named 'apply_patch'.
    """

    def list_changed_files(self, ref: str) -> list[str]:
        """Return list of file paths changed in the given commit/ref."""

    def read_file_at_ref(self, path: str, ref: str) -> str:
        """Return file contents at the given ref."""

    def current_branch(self) -> str:
        """Return current branch name."""


@runtime_checkable
class EmbeddingPort(Protocol):
    """Text embedding contract.

    Implementations must return a fixed-length list of floats for the same input text.
    """

    def embed_text(self, text: str) -> list[float]:
        """Return embedding vector for the provided text."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a batch of texts in the same order."""


@runtime_checkable
class StoragePort(Protocol):
    """Generic key-value storage contract for caching and RAG artifacts."""

    def put(self, key: str, value: bytes, ttl_seconds: int | None = None) -> None:
        """Store value under key. Overwrite if exists."""

    def get(self, key: str) -> bytes | None:
        """Return value or None if missing."""

    def delete(self, key: str) -> None:
        """Delete key if exists."""

    def list_keys(self) -> list[str]:
        """Return all keys in storage."""


@runtime_checkable
class LoggerPort(Protocol):
    """Minimal structured logging contract used by application code."""

    def info(self, message: str, **fields: Any) -> None: ...

    def debug(self, message: str, **fields: Any) -> None: ...

    def warning(self, message: str, **fields: Any) -> None: ...

    def error(self, message: str, **fields: Any) -> None: ...
