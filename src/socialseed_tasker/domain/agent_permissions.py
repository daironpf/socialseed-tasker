"""Explicit permission contract for agent profiles (issue #612).

The profile declares four independent capabilities: reading, proposing
changes, applying changes and executing catalog tools. Values are explicit;
an absent or empty list grants nothing. ``write_access`` is kept as a legacy
write-scope hint and never expands these capabilities on its own.

Resource scopes are intentionally a small domain vocabulary. They do not
include database/Cypher access: tools are the only way to request an action,
and each tool is validated against its catalog separately.
"""

from __future__ import annotations

from collections.abc import Iterable

AGENT_RESOURCE_SCOPES: tuple[str, ...] = (
    "repository",
    "documentation",
    "tests",
    "issues",
    "workflows",
    "graph",
    "configuration",
)

_RESOURCE_SCOPE_SET = frozenset(AGENT_RESOURCE_SCOPES)


def normalize_resource_scopes(values: Iterable[str]) -> list[str]:
    """Return unique, trimmed resource scopes or raise for an unknown one.

    Empty entries and scopes outside :data:`AGENT_RESOURCE_SCOPES` are
    rejected instead of being interpreted as broader access. Duplicates are
    collapsed while preserving the client's order.
    """
    normalized: list[str] = []
    for raw in values:
        value = str(raw).strip()
        if not value:
            raise ValueError("resource:<empty>")
        if value not in _RESOURCE_SCOPE_SET:
            raise ValueError(f"resource:{value}")
        if value not in normalized:
            normalized.append(value)
    return normalized


def normalize_tool_slugs(
    values: Iterable[str], allowed: Iterable[str] | None = None
) -> list[str]:
    """Return unique, trimmed tool slugs or raise for an unknown/empty one.

    ``allowed`` is optional so request schemas can normalize without loading
    the catalog; persistence and policy composition always pass the known
    slugs and therefore fail closed for unknown tools.
    """
    allowed_set = frozenset(allowed) if allowed is not None else None
    normalized: list[str] = []
    for raw in values:
        value = str(raw).strip()
        if not value:
            raise ValueError("tool:<empty>")
        if allowed_set is not None and value not in allowed_set:
            raise ValueError(f"tool:{value}")
        if value not in normalized:
            normalized.append(value)
    return normalized
