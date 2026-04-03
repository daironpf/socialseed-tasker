"""Neo4j repository implementations.

Implements TaskRepositoryInterface using Neo4j as the persistence engine.
Uses the synchronous Neo4j driver for simplicity and reliability.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.storage.graph_database import queries
from socialseed_tasker.storage.graph_database.driver import SchemaError

if TYPE_CHECKING:
    from socialseed_tasker.storage.graph_database.driver import Neo4jDriver

UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _is_valid_uuid(value: str) -> bool:
    """Check if string is a valid UUID format."""
    return UUID_PATTERN.match(value) is not None


def _normalize_id(value: str | UUID) -> str:
    """Ensure ID is always returned as a string."""
    if isinstance(value, UUID):
        return str(value)
    return str(value)


def _validate_id(value: str | UUID, field_name: str = "id") -> str:
    """Validate and normalize an ID to string format.

    Args:
        value: The ID value to validate
        field_name: Name of the field for error messages

    Returns:
        Normalized string ID

    Raises:
        ValueError: If the value is not a valid UUID string or UUID object
    """
    if isinstance(value, UUID):
        return str(value)

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or UUID, got {type(value).__name__}")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")

    if _is_valid_uuid(normalized):
        return normalized.lower()

    raise ValueError(f"{field_name} must be a valid UUID format, got: {normalized[:8]}...")


def _node_to_issue(node) -> Issue:
    """Convert a Neo4j node to a domain Issue."""
    data = dict(node)
    return Issue(
        id=_normalize_id(data["id"]),
        title=data["title"],
        description=data.get("description", ""),
        status=IssueStatus(data.get("status", "OPEN")),
        priority=data.get("priority", "MEDIUM"),
        component_id=_normalize_id(data["component_id"]),
        labels=data.get("labels", []),
        dependencies=[_normalize_id(d) for d in data.get("dependencies", [])],
        blocks=[_normalize_id(b) for b in data.get("blocks", [])],
        affects=[_normalize_id(a) for a in data.get("affects", [])],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        closed_at=data.get("closed_at"),
        architectural_constraints=data.get("architectural_constraints", []),
    )


def _node_to_component(node) -> Component:
    """Convert a Neo4j node to a domain Component."""
    data = dict(node)
    return Component(
        id=_normalize_id(data["id"]),
        name=data["name"],
        description=data.get("description"),
        project=data["project"],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InvalidIdError(ValueError):
    """Raised when an ID fails validation."""

    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid {field} '{value[:8]}...': {reason}")


def _ensure_string_id(value: str | UUID, field_name: str = "id") -> str:
    """Validate and convert ID to string with strict validation.

    Args:
        value: The ID value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated and normalized string ID

    Raises:
        InvalidIdError: If the value fails validation
    """
    try:
        return _validate_id(value, field_name)
    except ValueError as exc:
        raise InvalidIdError(field_name, str(value)[:8], str(exc)) from exc


class Neo4jTaskRepository(TaskRepositoryInterface):
    """Neo4j implementation of TaskRepositoryInterface.

    Intent: Persist issues and components in a Neo4j graph database.
    Business Value: Enables efficient graph traversals for dependency
    analysis, root-cause tracing, and impact assessment.
    """

    def __init__(self, driver: Neo4jDriver) -> None:
        self._driver = driver

    def _ensure_schema_ready(self) -> None:
        """Verify schema is initialized before any operation."""
        if not self._driver.is_schema_ready:
            try:
                self._driver.verify_schema()
            except SchemaError as exc:
                raise RuntimeError(f"Neo4j schema not ready. Run driver.connect() first. Details: {exc}") from exc

    def _normalize_issue_id(self, issue_id: str | UUID) -> str:
        """Normalize and validate issue ID to string format."""
        return _ensure_string_id(issue_id, "issue_id")

    def _normalize_component_id(self, component_id: str | UUID) -> str:
        """Normalize and validate component ID to string format."""
        return _ensure_string_id(component_id, "component_id")

    # -- Component CRUD ------------------------------------------------------

    def create_component(self, component: Component) -> None:
        self._ensure_schema_ready()
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_COMPONENT,
                id=str(component.id),
                name=component.name,
                description=component.description,
                project=component.project,
                created_at=component.created_at.isoformat(),
                updated_at=component.updated_at.isoformat(),
            )

    def get_component(self, component_id: str) -> Component | None:
        self._ensure_schema_ready()
        normalized_id = self._normalize_component_id(component_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_COMPONENT, id=normalized_id)
            record = result.single()
            return _node_to_component(record["c"]) if record else None

    def list_components(self, project: str | None = None) -> list[Component]:
        self._ensure_schema_ready()
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_COMPONENTS, project=project)
            return [_node_to_component(r["c"]) for r in result]

    # -- Issue CRUD ----------------------------------------------------------

    def create_issue(self, issue: Issue) -> None:
        self._ensure_schema_ready()
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_ISSUE,
                id=str(issue.id),
                title=issue.title,
                description=issue.description,
                status=issue.status.value,
                priority=issue.priority.value,
                component_id=str(issue.component_id),
                labels=issue.labels,
                dependencies=[str(d) for d in issue.dependencies],
                blocks=[str(b) for b in issue.blocks],
                affects=[str(a) for a in issue.affects],
                created_at=issue.created_at.isoformat(),
                updated_at=issue.updated_at.isoformat(),
                closed_at=issue.closed_at.isoformat() if issue.closed_at else None,
                architectural_constraints=issue.architectural_constraints,
            )

    def get_issue(self, issue_id: str) -> Issue | None:
        self._ensure_schema_ready()
        normalized_id = self._normalize_issue_id(issue_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUE, id=normalized_id)
            record = result.single()
            return _node_to_issue(record["i"]) if record else None

    def update_issue(self, issue_id: str, updates: dict) -> Issue:
        self._ensure_schema_ready()
        normalized_id = self._normalize_issue_id(issue_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.UPDATE_ISSUE,
                id=normalized_id,
                updates=updates,
                updated_at=_now_iso(),
            )
            record = result.single()
            return _node_to_issue(record["i"])

    def close_issue(self, issue_id: str) -> Issue:
        self._ensure_schema_ready()
        normalized_id = self._normalize_issue_id(issue_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.CLOSE_ISSUE,
                id=normalized_id,
                closed_at=_now_iso(),
                updated_at=_now_iso(),
            )
            record = result.single()
            return _node_to_issue(record["i"])

    def delete_issue(self, issue_id: str) -> None:
        self._ensure_schema_ready()
        normalized_id = self._normalize_issue_id(issue_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_ISSUE, id=normalized_id)

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
    ) -> list[Issue]:
        self._ensure_schema_ready()
        normalized_component = self._normalize_component_id(component_id) if component_id else None
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.LIST_ISSUES,
                component_id=normalized_component,
                status=status.value if status else None,
            )
            return [_node_to_issue(r["i"]) for r in result]

    # -- Dependency management -----------------------------------------------

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        self._ensure_schema_ready()
        normalized_issue = self._normalize_issue_id(issue_id)
        normalized_dep = self._normalize_issue_id(depends_on_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.ADD_DEPENDENCY,
                issue_id=normalized_issue,
                depends_on_id=normalized_dep,
            )

    def remove_dependency(self, issue_id: str, depends_on_id: str) -> None:
        self._ensure_schema_ready()
        normalized_issue = self._normalize_issue_id(issue_id)
        normalized_dep = self._normalize_issue_id(depends_on_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.REMOVE_DEPENDENCY,
                issue_id=normalized_issue,
                depends_on_id=normalized_dep,
            )

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        self._ensure_schema_ready()
        normalized_id = self._normalize_issue_id(issue_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_DEPENDENCIES, issue_id=normalized_id)
            return [_node_to_issue(r["target"]) for r in result]

    def get_dependents(self, issue_id: str) -> list[Issue]:
        self._ensure_schema_ready()
        normalized_id = self._normalize_issue_id(issue_id)
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_DEPENDENTS, issue_id=normalized_id)
            return [_node_to_issue(r["source"]) for r in result]
