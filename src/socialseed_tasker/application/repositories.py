"""Repository interfaces (Protocols) for domain persistence and graph queries."""

from __future__ import annotations

from typing import Protocol

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO, IssueSummary


class IssueRepository(Protocol):
    """Repository contract for Issue persistence.

    Implementations must:
    - Persist IssueDTO objects.
    - Return IssueDTO on read operations or None if not found.
    - Raise GraphPortError or a subclass for persistence-related failures.
    """

    def save(self, issue: IssueDTO) -> None:
        """Persist or update the issue."""

    def get(self, issue_id: str) -> IssueDTO | None:
        """Return IssueDTO or None if not found."""

    def list(self, status: str | None = None) -> list[IssueSummary]:
        """Return summaries of issues, optionally filtered by status."""

    def delete(self, issue_id: str) -> None:
        """Delete issue by id. No-op if missing."""


class GraphRepository(Protocol):
    """Repository contract for graph queries and dependency traversal.

    Implementations must:
    - Provide deterministic traversal results.
    - Return DependencyEdge objects for dependency queries.
    - Raise GraphPortError for graph-related failures.
    """

    def add_dependency(self, edge: DependencyEdge) -> None:
        """Create a dependency edge between issues."""

    def get_dependencies(self, issue_id: str, depth: int = 1) -> list[DependencyEdge]:
        """Return dependency edges reachable from issue_id up to depth."""

    def find_impact_set(self, issue_id: str, max_depth: int = 5) -> list[str]:
        """Return list of issue ids impacted by changes to issue_id (transitive closure)."""
