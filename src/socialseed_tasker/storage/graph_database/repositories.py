"""Neo4j repository implementations.

Implements TaskRepositoryInterface using Neo4j as the persistence engine.
Uses the synchronous Neo4j driver for simplicity and reliability.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.storage.graph_database import queries

if TYPE_CHECKING:
    from socialseed_tasker.storage.graph_database.driver import Neo4jDriver


def _node_to_issue(node: dict[str, Any]) -> Issue:
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
        created_at=data.get("created_at") or datetime.now(timezone.utc),
        updated_at=data.get("updated_at") or datetime.now(timezone.utc),
        closed_at=data.get("closed_at"),
        architectural_constraints=data.get("architectural_constraints", []),
        agent_working=data.get("agent_working", False),
    )


def _node_to_component(node: dict[str, Any]) -> Component:
    """Convert a Neo4j node to a domain Component."""
    data = dict(node)
    return Component(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        project=data["project"],
        created_at=data.get("created_at") or datetime.now(timezone.utc),
        updated_at=data.get("updated_at") or datetime.now(timezone.utc),
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

    def update_component(self, component_id: str, updates: dict[str, Any]) -> Component:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.UPDATE_COMPONENT,
                id=component_id,
                updates=updates,
                updated_at=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Component {component_id} not found")
            return _node_to_component(record["c"])

    def delete_component(self, component_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_COMPONENT, id=component_id)

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
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(record["i"])

    def update_issue(self, issue_id: str, updates: dict[str, Any]) -> Issue:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates=updates,
                updated_at=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
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
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(record["i"])

    def delete_issue(self, issue_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_ISSUE, id=issue_id)

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.LIST_ISSUES,
                component_id=component_id,
                status=status.value if status else None,
                project=project,
            )
            issues = []
            for r in result:
                issue = _node_to_issue(r["i"])
                dep_ids = r.get("dep_ids") or []
                blocked_ids = r.get("blocked_ids") or []
                updates: dict[str, Any] = {}
                if dep_ids:
                    updates["dependencies"] = dep_ids
                if blocked_ids:
                    updates["blocks"] = blocked_ids
                if updates:
                    issue = issue.model_copy(update=updates)
                issues.append(issue)
            return issues

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

    def get_blocked_issues(self) -> list[Issue]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                """
                MATCH (i:Issue {status: 'OPEN'})-[:DEPENDS_ON]->(d:Issue {status: 'OPEN'})
                RETURN DISTINCT i
                """
            )
            return [_node_to_issue(r["i"]) for r in result]

    def get_workable_issues(
        self,
        priority: str | None = None,
        component_id: str | None = None,
    ) -> list[Issue]:
        """Return issues that are ready to work on.

        An issue is workable if:
        - status != CLOSED
        - All its dependencies are CLOSED or it has no dependencies
        """
        with self._driver.driver.session(database=self._driver.database) as session:
            cypher = """
            MATCH (i:Issue)
            WHERE i.status <> 'CLOSED'
            OPTIONAL MATCH (i)-[:DEPENDS_ON]->(d:Issue)
            WITH i, COLLECT(DISTINCT d.status) AS dep_statuses
            WHERE ALL(status IN dep_statuses WHERE status = 'CLOSED') OR size(dep_statuses) = 0
            """
            params: dict[str, Any] = {}

            if priority:
                cypher += " AND i.priority = $priority"
                params["priority"] = priority

            if component_id:
                cypher += " AND i.component_id = $component_id"
                params["component_id"] = component_id

            cypher += " RETURN i"
            result = session.run(cypher, params)
            return [_node_to_issue(r["i"]) for r in result]

    # -- Transactions ----------------------------------------------------------

    @contextmanager
    def transaction(self):  # type: ignore[misc]
        """Execute Neo4j operations atomically using a real transaction."""
        with self._driver.driver.session(database=self._driver.database) as session:
            tx = session.begin_transaction()
            try:
                yield tx
                tx.commit()
            except Exception:
                tx.rollback()
                raise

    def reset_data(self, scope: str = "all") -> dict[str, int]:
        """Reset data in the repository."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result: dict[str, int] = {}

            if scope in ("all", "issues"):
                res = session.run("MATCH (i:Issue) DETACH DELETE i RETURN count(*) as count")
                result["issues_deleted"] = res.single()["count"] if res.single() else 0

            if scope in ("all", "components"):
                res = session.run("MATCH (c:Component) DETACH DELETE c RETURN count(*) as count")
                result["components_deleted"] = res.single()["count"] if res.single() else 0

            return result
