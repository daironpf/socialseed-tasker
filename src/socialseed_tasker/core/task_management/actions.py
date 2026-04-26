"""Core domain actions - create, close, move tasks and manage dependencies.

This module defines the repository interface contract and pure domain logic
actions that enforce business rules regardless of storage backend.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol

from socialseed_tasker.core.task_management.constraints import (
    Constraint,
    ConstraintCategory,
    ConstraintConfig,
    ConstraintValidationResult,
    ConstraintViolation,
)
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

    def __init__(self, issue_id: str, depends_on_id: str, cycle_path: list[str] | None = None) -> None:
        if cycle_path:
            path_str = " -> ".join(cycle_path)
            super().__init__(
                f"Adding dependency from '{issue_id}' to '{depends_on_id}' would create a cycle: {path_str}"
            )
        else:
            super().__init__(
                f"Adding dependency from '{issue_id}' to '{depends_on_id}' would create a circular dependency"
            )
        self.cycle_path = cycle_path


class IssueAlreadyClosedError(Exception):
    """Raised when attempting to close an issue that is already closed."""

    def __init__(self, issue_id: str) -> None:
        super().__init__(f"Issue '{issue_id}' is already closed")


class PolicyViolationError(Exception):
    """Raised when an action violates an architectural policy."""

    def __init__(self, policy_name: str, rule_type: str, message: str, suggestion: str = "") -> None:
        super().__init__(f"Policy violation: {policy_name} - {message}")
        self.policy_name = policy_name
        self.rule_type = rule_type
        self.message = message
        self.suggestion = suggestion


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
        statuses: list[str] | None = None,
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

    def add_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        """Create a [:DEPENDS_ON] relationship between components."""

    def remove_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        """Remove a [:DEPENDS_ON] relationship between components."""

    def get_component_dependencies(self, component_id: str) -> list[Component]:
        """Get components that this component depends on."""

    def get_component_dependents(self, component_id: str) -> list[Component]:
        """Get components that depend on this component."""

    def create_epic(self, epic: Any) -> None:
        """Create a new epic."""

    def get_epic(self, epic_id: str) -> Any | None:
        """Get an epic by ID."""

    def list_epics(self) -> list[Any]:
        """List all epics."""

    def update_epic(self, epic_id: str, updates: dict) -> Any:
        """Update an epic."""

    def delete_epic(self, epic_id: str) -> None:
        """Delete an epic."""

    def link_issue_to_epic(self, issue_id: str, epic_id: str) -> None:
        """Link an issue to an epic."""

    def create_objective(self, objective: Any) -> None:
        """Create a new objective."""

    def get_objective(self, objective_id: str) -> Any | None:
        """Get an objective by ID."""

    def list_objectives(self) -> list[Any]:
        """List all objectives."""

    def update_objective(self, objective_id: str, updates: dict) -> Any:
        """Update an objective."""

    def delete_objective(self, objective_id: str) -> None:
        """Delete an objective."""

    def link_epic_to_objective(self, epic_id: str, objective_id: str) -> None:
        """Link an epic to an objective."""

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

    def start_agent_work(self, issue_id: str, agent_id: str) -> Issue:
        """Start agent work on an issue."""

    def finish_agent_work(self, issue_id: str) -> Issue:
        """Finish agent work on an issue."""

    def get_cost_per_component(self) -> list[dict]:
        """Get cost breakdown by component for closed issues."""

    def get_cost_per_epic(self) -> list[dict]:
        """Get cost breakdown by epic for closed issues."""

    def get_cost_per_project(self) -> list[dict]:
        """Get cost breakdown by project for closed issues."""

    def get_cost_summary(self) -> dict:
        """Get overall cost summary."""

    def get_agent_status(self, issue_id: str) -> dict[str, Any]:
        """Get agent work status for an issue."""

    # -- Constraints -----------------------------------------------------------

    def create_constraint(self, constraint: Constraint) -> None:
        """Persist a new constraint."""

    def list_constraints(self, category: str | None = None) -> list[Constraint]:
        """List constraints, optionally filtered by category."""

    def get_constraint(self, constraint_id: str) -> Constraint | None:
        """Retrieve a constraint by ID."""

    def delete_constraint(self, constraint_id: str) -> None:
        """Permanently remove a constraint."""

    def update_constraint(self, constraint_id: str, updates: dict) -> Constraint:
        """Update a constraint."""

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

        cycle_path = _would_create_cycle(repository, issue_id, depends_on_id)
        if cycle_path:
            raise CircularDependencyError(issue_id, depends_on_id, cycle_path)

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
    """Reset data in the repository."""

    if scope not in ("all", "issues", "components"):
        raise ValueError("scope must be 'all', 'issues', or 'components'")

    return repository.reset_data(scope)


# ---------------------------------------------------------------------------
# Policy validation
# ---------------------------------------------------------------------------


def validate_action_against_policies(
    repository: TaskRepositoryInterface,
    action_type: str,
    action_data: dict,
    policy_engine: Any = None,
) -> None:
    """Validate an action against defined policies.

    Raises PolicyViolationError if the action violates any policy.
    """
    if policy_engine is None:
        return

    from socialseed_tasker.core.project_analysis.policy import PolicyEngine

    if not isinstance(policy_engine, PolicyEngine):
        return

    if action_type == "add_dependency":
        issue_id = action_data.get("issue_id")
        depends_on_id = action_data.get("depends_on_id")

        if issue_id and depends_on_id:
            issue = repository.get_issue(issue_id)
            target = repository.get_issue(depends_on_id)

            if issue and target:
                from_component = repository.get_component(str(issue.component_id))
                to_component = repository.get_component(str(target.component_id))

                result = policy_engine.validate_dependency(
                    from_component_name=from_component.name if from_component else "",
                    from_component_type=from_component.project if from_component else "",
                    from_labels=issue.labels,
                    to_component_name=to_component.name if to_component else "",
                    to_component_type=to_component.project if to_component else "",
                    to_labels=target.labels,
                )

                if result.has_violations:
                    violation = result.violations[0]
                    raise PolicyViolationError(
                        policy_name=violation.policy_name,
                        rule_type=violation.rule_type.value,
                        message=violation.message,
                        suggestion=violation.suggestion,
                    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _would_create_cycle(
    repository: TaskRepositoryInterface,
    issue_id: str,
    depends_on_id: str,
) -> list[str]:
    """Check if adding issue_id -> depends_on_id would create a cycle.

    Uses BFS to check if depends_on_id can already reach issue_id through
    existing [:DEPENDS_ON] edges.
    Returns the cycle path if a cycle is found, empty list otherwise.
    """
    visited: set[str] = set()
    queue = deque([(depends_on_id, [depends_on_id])])

    while queue:
        current, path = queue.popleft()
        if current == issue_id:
            return path + [issue_id]
        if current in visited:
            continue
        visited.add(current)

        for dep in repository.get_dependencies(current):
            dep_key = str(dep.id)
            if dep_key not in visited:
                queue.append((dep_key, path + [dep_key]))

    return []


# ---------------------------------------------------------------------------
# Constraint actions
# ---------------------------------------------------------------------------


class ConstraintNotFoundError(Exception):
    """Raised when a constraint with the given ID does not exist."""

    def __init__(self, constraint_id: str) -> None:
        super().__init__(f"Constraint with id '{constraint_id}' was not found")


def create_constraint_action(
    repository: TaskRepositoryInterface,
    constraint: Constraint,
) -> Constraint:
    """Create a new constraint after validating inputs.

    Returns:
        The created constraint
    """
    repository.create_constraint(constraint)
    return constraint


def list_constraints_action(
    repository: TaskRepositoryInterface,
    category: str | None = None,
) -> list[Constraint]:
    """List constraints, optionally filtered by category."""
    return repository.list_constraints(category=category)


def get_constraint_action(
    repository: TaskRepositoryInterface,
    constraint_id: str,
) -> Constraint:
    """Get a constraint by ID or raise not found."""
    constraint = repository.get_constraint(constraint_id)
    if constraint is None:
        raise ConstraintNotFoundError(constraint_id)
    return constraint


def delete_constraint_action(
    repository: TaskRepositoryInterface,
    constraint_id: str,
) -> None:
    """Delete a constraint by ID."""
    constraint = repository.get_constraint(constraint_id)
    if constraint is None:
        raise ConstraintNotFoundError(constraint_id)
    repository.delete_constraint(constraint_id)


def load_constraints_from_config_action(
    repository: TaskRepositoryInterface,
    config: ConstraintConfig,
) -> dict[str, int]:
    """Load constraints from config file, replacing existing ones.

    Returns:
        Dict with counts of created/updated constraints
    """
    from socialseed_tasker.core.task_management.constraints import ConstraintStatus

    existing = repository.list_constraints()
    for c in existing:
        repository.delete_constraint(str(c.id))

    constraints = config.to_constraints()
    for constraint in constraints:
        # Constraint is frozen=True, use model_copy to create active version
        active_constraint = constraint.model_copy(update={"status": ConstraintStatus.ACTIVE})
        repository.create_constraint(active_constraint)

    return {
        "created": len(constraints),
        "deleted": len(existing),
    }


def validate_constraints_action(
    repository: TaskRepositoryInterface,
) -> ConstraintValidationResult:
    """Validate all active constraints against current state.

    Returns:
        Validation result with any violations
    """
    constraints = repository.list_constraints()
    violations: list[ConstraintViolation] = []

    for constraint in constraints:
        if constraint.category == ConstraintCategory.DEPENDENCIES and constraint.rule_type == "max_depth":
            if constraint.max_depth:
                depth = _check_max_dependency_depth(repository, constraint.max_depth)
                if depth > constraint.max_depth:
                    violations.append(
                        ConstraintViolation(
                            constraint_id=constraint.id,
                            constraint_description=constraint.description,
                            level=constraint.level,
                            category=constraint.category,
                            affected_resource="dependency_graph",
                            message=f"Dependency depth {depth} exceeds max {constraint.max_depth}",
                            suggestion="Restructure dependencies to reduce depth",
                        )
                    )

    return ConstraintValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
    )


def _check_max_dependency_depth(repository: TaskRepositoryInterface, max_depth: int) -> int:
    """Check max dependency depth in the repository."""
    issues = repository.list_issues()
    max_found = 0

    for issue in issues:
        depth = _get_dependency_depth(repository, str(issue.id), set())
        max_found = max(max_found, depth)

    return max_found


def _get_dependency_depth(repository: TaskRepositoryInterface, issue_id: str, visited: set[str]) -> int:
    """Get the max depth of dependencies for an issue."""
    if issue_id in visited:
        return 0
    visited.add(issue_id)

    deps = repository.get_dependencies(issue_id)
    if not deps:
        return 0

    max_depth = 0
    for dep in deps:
        dep_depth = _get_dependency_depth(repository, str(dep.id), visited.copy())
        max_depth = max(max_depth, dep_depth + 1)

    return max_depth


def check_soft_constraints_for_closure(
    repository: TaskRepositoryInterface,
    issue_id: str,
) -> list[ConstraintViolation]:
    """Check soft constraints before allowing issue closure.

    Returns list of violated soft constraints - if any exist, the issue
    cannot be closed until the agent confirms compliance.
    """
    constraints = repository.list_constraints()
    violations: list[ConstraintViolation] = []

    for constraint in constraints:
        if constraint.level == "soft" and constraint.status == "active":
            violations.append(
                ConstraintViolation(
                    constraint_id=constraint.id,
                    constraint_description=constraint.description,
                    level=constraint.level,
                    category=constraint.category,
                    affected_resource=issue_id,
                    message=f"Soft constraint '{constraint.description}' may be violated",
                    suggestion="Confirm compliance or document why this constraint does not apply",
                )
            )

    return violations
