"""Neo4j repository implementations.

Implements TaskRepositoryInterface using Neo4j as the persistence engine.
Uses the synchronous Neo4j driver for simplicity and reliability.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.storage.graph_database import queries

if TYPE_CHECKING:
    from socialseed_tasker.storage.graph_database.driver import Neo4jDriver


def _node_to_issue(node) -> Issue:
    """Convert a Neo4j node to a domain Issue."""
    data = dict(node)
    return Issue(
        id=data["id"],
        title=data["title"],
        description=data.get("description", ""),
        status=IssueStatus(data.get("status", "OPEN")),
        priority=data.get("priority", "MEDIUM"),
        component_id=data["component_id"],
        labels=data.get("labels", []),
        dependencies=data.get("dependencies", []),
        blocks=data.get("blocks", []),
        affects=data.get("affects", []),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        closed_at=data.get("closed_at"),
        architectural_constraints=data.get("architectural_constraints", []),
    )


def _node_to_component(node) -> Component:
    """Convert a Neo4j node to a domain Component."""
    data = dict(node)
    return Component(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        project=data["project"],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Neo4jTaskRepository(TaskRepositoryInterface):
    """Neo4j implementation of TaskRepositoryInterface.

    Intent: Persist issues and components in a Neo4j graph database.
    Business Value: Enables efficient graph traversals for dependency
    analysis, root-cause tracing, and impact assessment.
    """

    def __init__(self, driver: Neo4jDriver) -> None:
        self._driver = driver

    # -- Component CRUD ------------------------------------------------------

    def create_component(self, component: Component) -> None:
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
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_COMPONENT, id=component_id)
            record = result.single()
            return _node_to_component(record["c"]) if record else None

    def list_components(self, project: str | None = None) -> list[Component]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_COMPONENTS, project=project)
            return [_node_to_component(r["c"]) for r in result]

    # -- Issue CRUD ----------------------------------------------------------

    def create_issue(self, issue: Issue) -> None:
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
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUE, id=issue_id)
            record = result.single()
            return _node_to_issue(record["i"]) if record else None

    def update_issue(self, issue_id: str, updates: dict) -> Issue:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates=updates,
                updated_at=_now_iso(),
            )
            record = result.single()
            return _node_to_issue(record["i"])

    def close_issue(self, issue_id: str) -> Issue:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.CLOSE_ISSUE,
                id=issue_id,
                closed_at=_now_iso(),
                updated_at=_now_iso(),
            )
            record = result.single()
            return _node_to_issue(record["i"])

    def delete_issue(self, issue_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_ISSUE, id=issue_id)

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
    ) -> list[Issue]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.LIST_ISSUES,
                component_id=component_id,
                status=status.value if status else None,
            )
            return [_node_to_issue(r["i"]) for r in result]

    # -- Dependency management -----------------------------------------------

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.ADD_DEPENDENCY,
                issue_id=issue_id,
                depends_on_id=depends_on_id,
            )

    def remove_dependency(self, issue_id: str, depends_on_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.REMOVE_DEPENDENCY,
                issue_id=issue_id,
                depends_on_id=depends_on_id,
            )

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_DEPENDENCIES, issue_id=issue_id)
            return [_node_to_issue(r["target"]) for r in result]

    def get_dependents(self, issue_id: str) -> list[Issue]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_DEPENDENTS, issue_id=issue_id)
            return [_node_to_issue(r["source"]) for r in result]
