"""Domain DTOs used by repository interfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class IssueDTO:
    """Full issue data transfer object."""

    id: str
    title: str
    description: str
    status: str
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class IssueSummary:
    """Lightweight issue summary for listing."""

    id: str
    title: str
    status: str


@dataclass(frozen=True)
class DependencyEdge:
    """Directed dependency relationship between two issues."""

    from_issue_id: str
    to_issue_id: str
    relation: str
    metadata: Mapping[str, object] | None = None
