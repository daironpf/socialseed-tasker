"""Core domain actions - create, close, move tasks and manage dependencies.

This module defines the repository interface contract and pure domain logic
actions that enforce business rules regardless of storage backend.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol

from socialseed_tasker.core.task_management.entities import (
    Component,
    Issue,
    IssueStatus,
)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class IssueNotFoundError(Exception):
    """Raised when an issue with the given ID does not exist."""

    def __init__(self, issue_id: str) -> None:
        super().__init__(f"Issue with id '{issue_id}' was not found")


class ComponentNotFoundError(Exception):
    """Raised when a component with the given ID does not exist."""

    def __init__(self, component_id: str) -> None:
        super().__init__(f"Component with id '{component_id}' was not found")


class CircularDependencyError(Exception):
    """Raised when adding a dependency would create a cycle in the graph."""

    def __init__(self, issue_id: str, depends_on_id: str) -> None:
        super().__init__(f"Adding dependency from '{issue_id}' to '{depends_on_id}' would create a circular dependency")


class IssueAlreadyClosedError(Exception):
    """Raised when attempting to close an issue that is already closed."""

    def __init__(self, issue_id: str) -> None:
        super().__init__(f"Issue '{issue_id}' is already closed")


class OpenDependenciesError(Exception):
    """Raised when closing an issue that still has open dependencies."""

    def __init__(self, issue_id: str, open_deps: list[str]) -> None:
        super().__init__(f"Cannot close issue '{issue_id}' because it still has open dependencies: {open_deps}")


# ---------------------------------------------------------------------------
# Repository interface
# ---------------------------------------------------------------------------


class TaskRepositoryInterface(Protocol):
    """Contract that all task storage backends must implement.

    Intent: Decouple business logic from persistence so the core domain
    can work with Neo4j, local files, or any future backend without changes.
    Business Value: Enables storage flexibility, testability via mocks, and
    gradual migration between backends.
    """

    # -- Issue CRUD ----------------------------------------------------------

    def create_issue(self, issue: Issue) -> None:
        """Persist a new issue."""

    def get_issue(self, issue_id: str) -> Issue | None:
        """Retrieve an issue by ID, or None if not found."""

    def update_issue(self, issue_id: str, updates: dict) -> Issue:
        """Apply partial updates and return the updated issue."""

    def close_issue(self, issue_id: str) -> Issue:
        """Transition an issue to CLOSED status."""

    def delete_issue(self, issue_id: str) -> None:
        """Permanently remove an issue and its relationships."""

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        """List issues with optional filters."""

    # -- Dependency management -----------------------------------------------

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        """Create a [:DEPENDS_ON] relationship."""

    def remove_dependency(self, issue_id: str, depends_on_id: str) -> None:
        """Remove a [:DEPENDS_ON] relationship."""

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        """Return issues that *issue_id* depends on."""

    def get_dependents(self, issue_id: str) -> list[Issue]:
        """Return issues that depend on *issue_id*."""

    def get_blocked_issues(self) -> list[Issue]:
        """Return all issues that are blocked by at least one open dependency."""

    def get_workable_issues(
        self,
        priority: str | None = None,
        component_id: str | None = None,
    ) -> list[Issue]:
        """Return all issues that can be worked on (not closed and all dependencies closed)."""

    # -- Component CRUD ------------------------------------------------------

    def create_component(self, component: Component) -> None:
        """Persist a new component."""

    def get_component(self, component_id: str) -> Component | None:
        """Retrieve a component by ID, or None if not found."""

    def list_components(self, project: str | None = None) -> list[Component]:
        """List components, optionally filtered by project."""

    def update_component(self, component_id: str, updates: dict) -> Component:
        """Apply partial updates and return the updated component."""

    def delete_component(self, component_id: str) -> None:
        """Permanently remove a component."""

    def get_component_by_name(self, name: str, project: str | None = None) -> Component | None:
        """Retrieve a component by exact name, optionally filtered by project."""

    def find_issues_by_title(
        self,
        title: str,
        component_id: str | None = None,
    ) -> list[Issue]:
        """Find issues by exact title, optionally filtered by component."""

    def add_reasoning_log(
        self,
        issue_id: str,
        context: str,
        reasoning: str,
        related_nodes: list[str] | None = None,
    ) -> Issue:
        """Add a reasoning log entry to an issue and return the updated issue."""

    def get_reasoning_logs(self, issue_id: str) -> list[dict[str, Any]]:
        """Get all reasoning log entries for an issue."""

    def update_manifest_todo(self, issue_id: str, todo: list[dict[str, str]]) -> Issue:
        """Update the manifest TODO list for an issue."""

    def update_manifest_files(self, issue_id: str, files: list[str]) -> Issue:
        """Update the manifest affected files list for an issue."""

    def update_manifest_notes(self, issue_id: str, notes: list[str]) -> Issue:
        """Update the manifest technical debt notes for an issue."""

    def get_manifest(self, issue_id: str) -> dict[str, Any]:
        """Get the full manifest for an issue."""

    def reset_data(self, scope: str = "all") -> dict[str, int]:
        """Reset data in the repository.

        Args:
            scope: What to reset - "all", "issues", or "components"

        Returns:
            Dict with counts of deleted items
        """

    # -- Transactions ----------------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Execute operations atomically.

        Usage:
            with repo.transaction():
                # do operations
        """
        yield


# ---------------------------------------------------------------------------
# Core actions
# ---------------------------------------------------------------------------


def create_issue_action(
    repository: TaskRepositoryInterface,
    title: str,
    component_id: str | None = None,
    description: str = "",
    priority: str = "MEDIUM",
    labels: list[str] | None = None,
    architectural_constraints: list[str] | None = None,
) -> tuple[Issue, list[str]]:
    """Create a new issue after validating inputs.

    Intent: Ensure every issue is valid and belongs to an existing component
    before persisting it. If no component is provided, creates or uses
    an 'uncategorized' component.
    Business Value: Prevents orphaned issues and enforces data quality at
    the domain boundary.

    Returns:
        Tuple of (Issue, warnings list)
    """
    from uuid import uuid4

    from socialseed_tasker.core.task_management.entities import Component, Issue, IssuePriority

    warnings: list[str] = []

    if component_id:
        component = repository.get_component(component_id)
        if component is None:
            raise ComponentNotFoundError(component_id)
    else:
        comp = repository.get_component_by_name("uncategorized", "system")
        if comp:
            component_id = str(comp.id)
            component = comp
        else:
            component = Component(
                id=uuid4(),
                name="uncategorized",
                project="system",
                description="Default component for issues without assignment",
            )
            repository.create_component(component)
            component_id = str(component.id)
            warnings.append("Created default 'uncategorized' component for unassigned issues")

    existing = repository.find_issues_by_title(title, component_id)
    if existing:
        existing_ids = [str(i.id) for i in existing]
        warnings.append(
            f"Issue with title '{title}' already exists in this component. Existing IDs: {', '.join(existing_ids)}"
        )

    issue = Issue(
        title=title,
        description=description,
        priority=IssuePriority(priority),
        component_id=component_id,
        labels=labels or [],
        architectural_constraints=architectural_constraints or [],
    )
    repository.create_issue(issue)
    return issue, warnings


def close_issue_action(
    repository: TaskRepositoryInterface,
    issue_id: str,
) -> Issue:
    """Close an issue after validating it has no open dependencies.

    Intent: Prevent closing issues that still depend on open work, which
    would leave the project in an inconsistent state.
    Business Value: Ensures work is truly complete before marking it done,
    reducing technical debt and hidden blockers.
    """
    with repository.transaction():
        issue = repository.get_issue(issue_id)
        if issue is None:
            raise IssueNotFoundError(issue_id)

        if issue.status == IssueStatus.CLOSED:
            raise IssueAlreadyClosedError(issue_id)

        open_deps = [dep.id for dep in repository.get_dependencies(issue_id) if dep.status != IssueStatus.CLOSED]
        if open_deps:
            raise OpenDependenciesError(issue_id, open_deps)

        return repository.close_issue(issue_id)


def move_issue_action(
    repository: TaskRepositoryInterface,
    issue_id: str,
    to_component_id: str,
) -> Issue:
    """Move an issue from its current component to another.

    Intent: Allow reorganising work across components while validating the
    target component exists.
    Business Value: Supports evolving project structure without losing
    issue history or relationships.
    """
    with repository.transaction():
        issue = repository.get_issue(issue_id)
        if issue is None:
            raise IssueNotFoundError(issue_id)

        target = repository.get_component(to_component_id)
        if target is None:
            raise ComponentNotFoundError(to_component_id)

        return repository.update_issue(issue_id, {"component_id": to_component_id})


def add_dependency_action(
    repository: TaskRepositoryInterface,
    issue_id: str,
    depends_on_id: str,
) -> None:
    """Add a [:DEPENDS_ON] relationship after checking for cycles.

    Intent: Link issues through dependencies while guaranteeing the graph
    remains acyclic.
    Business Value: Prevents infinite loops in dependency traversal and
    ensures the dependency graph stays analysable.
    """
    with repository.transaction():
        issue = repository.get_issue(issue_id)
        if issue is None:
            raise IssueNotFoundError(issue_id)

        target = repository.get_issue(depends_on_id)
        if target is None:
            raise IssueNotFoundError(depends_on_id)

        if issue_id == depends_on_id:
            raise CircularDependencyError(issue_id, depends_on_id)

        if _would_create_cycle(repository, issue_id, depends_on_id):
            raise CircularDependencyError(issue_id, depends_on_id)

        repository.add_dependency(issue_id, depends_on_id)


def remove_dependency_action(
    repository: TaskRepositoryInterface,
    issue_id: str,
    depends_on_id: str,
) -> None:
    """Remove a [:DEPENDS_ON] relationship.

    Intent: Allow restructuring dependencies when requirements change.
    Business Value: Keeps the dependency graph accurate as work evolves.
    """
    issue = repository.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    target = repository.get_issue(depends_on_id)
    if target is None:
        raise IssueNotFoundError(depends_on_id)

    repository.remove_dependency(issue_id, depends_on_id)


def get_blocked_issues_action(
    repository: TaskRepositoryInterface,
) -> list[Issue]:
    """Return all issues blocked by at least one open dependency.

    Intent: Surface work that cannot proceed because prerequisites are
    still open.
    Business Value: Gives teams visibility into bottlenecks so they can
    prioritise unblocking work.
    """
    return repository.get_blocked_issues()


def get_workable_issues_action(
    repository: TaskRepositoryInterface,
    priority: str | None = None,
    component_id: str | None = None,
) -> list[Issue]:
    """Return all issues that are ready to work on.

    Intent: Surface issues that are not blocked by open dependencies.
    This is the inverse of get_blocked_issues - it returns issues where
    status != CLOSED AND all dependencies are CLOSED.
    Business Value: Enables AI agents to efficiently find work without
    checking each issue's dependencies individually.
    """
    return repository.get_workable_issues(priority=priority, component_id=component_id)


def get_dependency_chain_action(
    repository: TaskRepositoryInterface,
    issue_id: str,
) -> list[Issue]:
    """Return the full transitive dependency chain for an issue.

    Intent: Discover every issue that must be completed before the given
    issue can be considered done.
    Business Value: Enables impact analysis, sprint planning, and root-cause
    tracing by revealing the complete dependency graph.
    """
    issue = repository.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    visited: set[str] = set()
    chain: list[Issue] = []
    queue = deque([str(issue_id)])

    while queue:
        current_id = queue.popleft()
        if current_id in visited:
            continue
        visited.add(current_id)

        if current_id != str(issue_id):
            dep_issue = repository.get_issue(current_id)
            if dep_issue is not None:
                chain.append(dep_issue)

        for dep in repository.get_dependencies(current_id):
            dep_id_str = str(dep.id)
            if dep_id_str not in visited:
                queue.append(dep_id_str)

    return chain


def update_component_action(
    repository: TaskRepositoryInterface,
    component_id: str,
    name: str | None = None,
    description: str | None = None,
    project: str | None = None,
) -> Component:
    """Update a component's fields.

    Intent: Allow modifying component metadata after creation.
    Business Value: Enables renaming, re-describing, or reassigning projects.
    """
    existing = repository.get_component(component_id)
    if existing is None:
        raise ComponentNotFoundError(component_id)

    updates: dict = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if project is not None:
        updates["project"] = project

    return repository.update_component(component_id, updates)


def delete_component_action(
    repository: TaskRepositoryInterface,
    component_id: str,
    force: bool = False,
) -> None:
    """Delete a component, optionally moving its issues to unassigned.

    Intent: Allow removing components that are no longer needed.
    Business Value: Keeps the component list clean and relevant.

    If force is False and the component has issues, raises an error.
    If force is True, the component is deleted regardless of issues.
    """
    existing = repository.get_component(component_id)
    if existing is None:
        raise ComponentNotFoundError(component_id)

    if not force:
        issues = repository.list_issues(component_id=component_id)
        if issues:
            raise ComponentHasIssuesError(
                component_id,
                [str(i.id) for i in issues],
            )

    repository.delete_component(component_id)


class ComponentHasIssuesError(Exception):
    """Raised when attempting to delete a component that has issues."""

    def __init__(self, component_id: str, issue_ids: list[str]) -> None:
        super().__init__(
            f"Cannot delete component '{component_id}' because it has {len(issue_ids)} issue(s): {issue_ids}"
        )


def reset_data_action(
    repository: TaskRepositoryInterface,
    scope: str = "all",
) -> dict[str, int]:
    """Reset data in the repository.

    Intent: Allow cleanup of all data for testing or demos.
    Business Value: Enables fresh start without manual cleanup or
    restarting the database.
    """
    if scope not in ("all", "issues", "components"):
        raise ValueError("scope must be 'all', 'issues', or 'components'")

    return repository.reset_data(scope)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _would_create_cycle(
    repository: TaskRepositoryInterface,
    issue_id: str,
    depends_on_id: str,
) -> bool:
    """Check if adding issue_id -> depends_on_id would create a cycle.

    Uses BFS to check if depends_on_id can already reach issue_id through
    existing [:DEPENDS_ON] edges.
    """
    visited: set[str] = set()
    queue = deque([depends_on_id])

    while queue:
        current = queue.popleft()
        if current == issue_id:
            return True
        if current in visited:
            continue
        visited.add(current)

        for dep in repository.get_dependencies(current):
            dep_key = str(dep.id)
            if dep_key not in visited:
                queue.append(dep_key)

    return False
