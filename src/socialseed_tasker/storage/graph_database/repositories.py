"""Neo4j repository implementations.

Implements TaskRepositoryInterface using Neo4j as the persistence engine.
Uses the synchronous Neo4j driver for simplicity and reliability.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.constraints import (
    Constraint,
    ConstraintCategory,
    ConstraintLevel,
    ConstraintStatus,
)
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.core.task_management.value_objects import ReasoningContext, ReasoningLogEntry
from socialseed_tasker.core.services.embedding_service import get_embedding_service
from socialseed_tasker.storage.graph_database import queries

if TYPE_CHECKING:
    from socialseed_tasker.storage.graph_database.driver import Neo4jDriver


class _ReasoningLogEntryDTO(BaseModel):
    id: str
    timestamp: str
    context: str
    reasoning: str
    related_nodes: list[str]


def _node_to_issue(node: dict[str, Any]) -> Issue:
    """Convert a Neo4j node to a domain Issue."""
    data = dict(node)
    reasoningLogs = []
    if "reasoningLogs" in data and data["reasoningLogs"]:
        for log_data in data["reasoningLogs"]:
            if isinstance(log_data, dict):
                reasoningLogs.append(
                    ReasoningLogEntry(
                        id=log_data.get("id"),
                        timestamp=datetime.fromisoformat(
                            log_data.get("timestamp", datetime.now(timezone.utc).isoformat())
                        ),
                        context=ReasoningContext(log_data.get("context", "architecture_choice")),
                        reasoning=log_data.get("reasoning", ""),
                        related_nodes=log_data.get("related_nodes", []),
                    )
                )
    return Issue(
        id=data["id"],
        title=data["title"],
        description=data.get("description", ""),
        status=IssueStatus(data.get("status", "OPEN")),
        priority=data.get("priority", "MEDIUM"),
        component_id=data.get("componentId") or data.get("component_id"),
        labels=data.get("labels", []),
        dependencies=data.get("dependencies", []),
        blocks=data.get("blocks", []),
        affects=data.get("affects", []),
        created_at=data.get("createdAt") or data.get("created_at") or datetime.now(timezone.utc),
        updated_at=data.get("updatedAt") or data.get("updated_at") or datetime.now(timezone.utc),
        closed_at=data.get("closedAt") or data.get("closed_at"),
        architectural_constraints=data.get("architecturalConstraints", []),
        agent_working=data.get("agentWorking", False),
        agent_started_at=data.get("agentStartedAt") or data.get("agent_started_at"),
        agent_finished_at=data.get("agentFinishedAt") or data.get("agent_finished_at"),
        agent_id=data.get("agentId") or data.get("agent_id"),
        reasoning_logs=reasoningLogs,
        manifest_todo=data.get("manifestTodo", []),
        manifest_files=data.get("manifestFiles", []),
        manifest_notes=data.get("manifestNotes", []),
        resolved_by_commit_sha=data.get("resolvedByCommitSha") or data.get("resolved_by_commit_sha"),
        resolution=data.get("resolution"),
    )


def _node_to_component(node: dict[str, Any]) -> Component:
    """Convert a Neo4j node to a domain Component."""
    data = dict(node)
    return Component(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        project=data["project"],
        created_at=data.get("createdAt") or data.get("created_at") or datetime.now(timezone.utc),
        updated_at=data.get("updatedAt") or data.get("updated_at") or datetime.now(timezone.utc),
    )


def _to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    return "".join(word.capitalize() if i > 0 else word for i, word in enumerate(string.split("_")))


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
                projectId=str(component.project_id) if component.project_id else None,
                createdAt=component.created_at.isoformat(),
                updatedAt=component.updated_at.isoformat(),
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

    def list_projects(self) -> list[str]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_PROJECTS)
            return [r["name"] for r in result]

    def list_project_nodes(self) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_PROJECT_NODES)
            projects = []
            for r in result:
                p = r["p"]
                projects.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "description": p.get("description"),
                    "repositoryUrl": p.get("repositoryUrl"),
                    "basePackage": p.get("basePackage"),
                    "visibility": p.get("visibility"),
                    "status": p.get("status"),
                    "techStack": p.get("techStack"),
                    "mainStack": p.get("mainStack"),
                    "architectureStyle": p.get("architectureStyle"),
                    "version": p.get("version"),
                    "conventionsUrl": p.get("conventionsUrl"),
                    "conventionsRules": p.get("conventionsRules"),
                    "lastFullScan": p.get("lastFullScan"),
                    "globalStatus": p.get("globalStatus"),
                    "createdAt": p.get("createdAt"),
                    "updatedAt": p.get("updatedAt"),
                })
            return projects

    def create_project_node(
        self,
        id: str,
        name: str,
        slug: str,
        description: str = "",
        repositoryUrl: str | None = None,
        basePackage: str | None = None,
        visibility: str = "PRIVATE",
        status: str = "ACTIVE",
        techStack: list | None = None,
        mainStack: list | None = None,
        architectureStyle: str | None = None,
        version: str = "0.0.1",
        conventionsUrl: str | None = None,
        conventionsRules: str | None = None,
        lastFullScan: str | None = None,
        globalStatus: str = "DEVELOPMENT",
    ) -> dict:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        params = {
            "id": id,
            "name": name,
            "slug": slug,
            "description": description,
            "repositoryUrl": repositoryUrl,
            "basePackage": basePackage,
            "visibility": visibility,
            "status": status,
            "techStack": techStack or [],
            "mainStack": mainStack or [],
            "architectureStyle": architectureStyle,
            "version": version,
            "conventionsUrl": conventionsUrl,
            "conventionsRules": conventionsRules,
            "lastFullScan": lastFullScan,
            "globalStatus": globalStatus,
            "createdAt": now,
            "updatedAt": now,
        }
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.CREATE_PROJECT, params)
            record = result.single()
            if record:
                p = record["p"]
                return {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "description": p.get("description"),
                }
            return None

    def get_component_by_name(self, name: str, project: str | None = None) -> Component | None:
        with self._driver.driver.session(database=self._driver.database) as session:
            if project:
                result = session.run(
                    "MATCH (c:Component {name: $name, project: $project}) RETURN c",
                    name=name,
                    project=project,
                )
            else:
                result = session.run(
                    "MATCH (c:Component {name: $name}) RETURN c",
                    name=name,
                )
            record = result.single()
            return _node_to_component(record["c"]) if record else None

    def update_component(self, component_id: str, updates: dict[str, Any]) -> Component:
        with self._driver.driver.session(database=self._driver.database) as session:
            # Translate snake_case keys to camelCase
            camel_updates = {_to_camel(k): v for k, v in updates.items()}
            result = session.run(
                queries.UPDATE_COMPONENT,
                id=component_id,
                updates=camel_updates,
                updatedAt=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Component {component_id} not found")
            return _node_to_component(record["c"])

    def delete_component(self, component_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_COMPONENT, id=componentId)

    def add_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.ADD_COMPONENT_DEPENDENCY,
                componentId=componentId,
                depends_on_id=depends_on_id,
            )

    def remove_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.REMOVE_COMPONENT_DEPENDENCY,
                componentId=componentId,
                depends_on_id=depends_on_id,
            )

    def get_component_dependencies(self, component_id: str) -> list[Component]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_COMPONENT_DEPENDENCIES,
                componentId=componentId,
            )
            return [_node_to_component(r["dep"]) for r in result]

    def get_component_dependents(self, component_id: str) -> list[Component]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_COMPONENT_DEPENDENTS,
                componentId=componentId,
            )
            return [_node_to_component(r["dependent"]) for r in result]

    # -- Issue CRUD ----------------------------------------------------------

    def create_issue(self, issue: Issue) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            reasoning_logs_data = []
            for log in issue.reasoning_logs:
                reasoning_logs_data.append(
                    {
                        "id": str(log.id),
                        "timestamp": log.timestamp.isoformat(),
                        "context": log.context.value,
                        "reasoning": log.reasoning,
                        "related_nodes": [str(n) for n in log.related_nodes],
                    }
                )
            session.run(
                queries.CREATE_ISSUE,
                id=str(issue.id),
                title=issue.title,
                description=issue.description,
                status=issue.status.value,
                priority=issue.priority.value,
                componentId=str(issue.component_id),
                labels=issue.labels,
                dependencies=[str(d) for d in issue.dependencies],
                blocks=[str(b) for b in issue.blocks],
                affects=[str(a) for a in issue.affects],
                createdAt=issue.created_at.isoformat(),
                updatedAt=issue.updated_at.isoformat(),
                closedAt=issue.closed_at.isoformat() if issue.closed_at else None,
                architecturalConstraints=issue.architectural_constraints,
                agentWorking=issue.agent_working,
                agentStartedAt=issue.agent_started_at.isoformat() if issue.agent_started_at else None,
                agentFinishedAt=issue.agent_finished_at.isoformat() if issue.agent_finished_at else None,
                agentId=issue.agent_id,
                reasoningLogs=reasoning_logs_data,
                manifestTodo=issue.manifest_todo,
                manifestFiles=issue.manifest_files,
                manifestNotes=issue.manifest_notes,
            )

            # Index for RAG (Native in Graph)
            embedding_service = get_embedding_service()
            if embedding_service.is_available():
                try:
                    text = issue.to_indexable_text()
                    embedding = embedding_service.generate(text)
                    if embedding:
                        session.run(
                            queries.UPDATE_ISSUE_EMBEDDING,
                            id=str(issue.id),
                            embedding=embedding,
                        )
                except Exception:
                    pass

    def get_issue(self, issue_id: str) -> Issue | None:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUE, id=issue_id)
            record = result.single()
            if record is None:
                return None
            return _node_to_issue(record["i"])

    def update_issue(self, issue_id: str, updates: dict[str, Any]) -> Issue:
        with self._driver.driver.session(database=self._driver.database) as session:
            # Translate snake_case keys to camelCase
            camel_updates = {_to_camel(k): v for k, v in updates.items()}
            result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates=camel_updates,
                updatedAt=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            issue = _node_to_issue(record["i"])

            # Index for RAG (Native in Graph)
            embedding_service = get_embedding_service()
            if embedding_service.is_available():
                try:
                    text = issue.to_indexable_text()
                    embedding = embedding_service.generate(text)
                    if embedding:
                        session.run(
                            queries.UPDATE_ISSUE_EMBEDDING,
                            id=issue_id,
                            embedding=embedding,
                        )
                except Exception:
                    pass

            return issue

    def close_issue(self, issue_id: str, commit_sha: str | None = None, resolution: str = "implemented") -> Issue:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.CLOSE_ISSUE,
                id=issue_id,
                closedAt=_now_iso(),
                updatedAt=_now_iso(),
                commitSha=commit_sha,
                resolution=resolution,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            issue = _node_to_issue(record["i"])

            # Index for RAG (Native in Graph)
            embedding_service = get_embedding_service()
            if embedding_service.is_available():
                try:
                    text = issue.to_indexable_text()
                    embedding = embedding_service.generate(text)
                    if embedding:
                        session.run(
                            queries.UPDATE_ISSUE_EMBEDDING,
                            id=issue_id,
                            embedding=embedding,
                        )
                except Exception:
                    pass

            return issue

    def delete_issue(self, issue_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_ISSUE, id=issue_id)

    def list_issues(
        self,
        component_id: str | None = None,
        statuses: list[str] | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.LIST_ISSUES,
                componentId=component_id,
                statuses=statuses or [],
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

    # -- CodeSymbol relationship (AFFECTS) --------------------------------------

    def add_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        """Link a CodeSymbol to an Issue (AFFECTS relationship)."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.ISSUE_AFFECTS_SYMBOL,
                issue_id=issue_id,
                symbol_id=symbol_id,
                closedAt=datetime.now(timezone.utc).isoformat(),
            )

    def get_affected_symbols(self, issue_id: str) -> list[dict[str, Any]]:
        """Get all CodeSymbols affected by an Issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                """
                MATCH (i:Issue {id: $issue_id})-[r:AFFECTS]->(s:CodeSymbol)
                RETURN s.id as id, s.name as name, s.symbolType as symbolType
                """,
                issue_id=issue_id,
            )
            return [
                {"id": r["id"], "name": r["name"], "symbol_type": r["symbolType"]}
                for r in result
            ]

    def get_issues_affecting_symbol(self, symbol_id: str) -> list[Issue]:
        """Get all Issues that affect a specific CodeSymbol."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                """
                MATCH (i:Issue)-[r:AFFECTS]->(s:CodeSymbol {id: $symbol_id})
                RETURN i
                """,
                symbol_id=symbol_id,
            )
            return [_node_to_issue(r["i"]) for r in result]

    def remove_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        """Remove AFFECTS relationship between Issue and CodeSymbol."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                """
                MATCH (i:Issue {id: $issue_id})-[r:AFFECTS]->(s:CodeSymbol {id: $symbol_id})
                DELETE r
                """,
                issue_id=issue_id,
                symbol_id=symbol_id,
            )

    def find_issues_by_title(
        self,
        title: str,
        component_id: str | None = None,
    ) -> list[Issue]:
        """Find issues by exact title, optionally filtered by component."""
        with self._driver.driver.session(database=self._driver.database) as session:
            if component_id:
                result = session.run(
                    """
                    MATCH (i:Issue {title: $title, componentId: $componentId})
                    RETURN i
                    """,
                    title=title,
                    componentId=component_id,
                )
            else:
                result = session.run(
                    """
                    MATCH (i:Issue {title: $title})
                    RETURN i
                    """,
                    title=title,
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
            WHERE size(dep_statuses) = 0 OR ALL(status IN dep_statuses WHERE status = 'CLOSED')
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

    # -- Reasoning log ---------------------------------------------------------

    def add_reasoning_log(
        self,
        issue_id: str,
        context: str,
        reasoning: str,
        related_nodes: list[str] | None = None,
    ) -> Issue:
        """Add a reasoning log entry to an issue and return the updated issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")

            node_data = dict(record["i"])
            existing_logs = node_data.get("reasoningLogs", [])
            new_log = {
                "id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context,
                "reasoning": reasoning,
                "related_nodes": related_nodes or [],
            }
            existing_logs.append(new_log)

            update_result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates={"reasoningLogs": existing_logs},
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def get_reasoning_logs(self, issue_id: str) -> list[dict[str, Any]]:
        """Get all reasoning log entries for an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return record["i"].get("reasoningLogs", [])

    # -- Manifest ---------------------------------------------------------------

    def update_manifest_todo(self, issue_id: str, todo: list[dict[str, str]]) -> Issue:
        """Update the manifest TODO list for an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")

            update_result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates={"manifestTodo": todo},
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def update_manifest_files(self, issue_id: str, files: list[str]) -> Issue:
        """Update the manifest affected files list for an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")

            update_result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates={"manifestFiles": files},
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def update_manifest_notes(self, issue_id: str, notes: list[str]) -> Issue:
        """Update the manifest technical debt notes for an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")

            update_result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates={"manifestNotes": notes},
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def get_manifest(self, issue_id: str) -> dict[str, Any]:
        """Get the full manifest for an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return {
                "todo": record["i"].get("manifestTodo", []),
                "files": record["i"].get("manifestFiles", []),
                "notes": record["i"].get("manifestNotes", []),
            }

    # -- Agent lifecycle --------------------------------------------------------

    def start_agent_work(self, issue_id: str, agent_id: str) -> Issue:
        """Start agent work on an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")

            node_data = dict(record["i"])
            if node_data.get("agentWorking", False):
                raise ValueError(f"Agent is already working on issue {issue_id}")

            update_result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates={
                    "agentWorking": True,
                    "agentStartedAt": _now_iso(),
                    "agentId": agentId,
                },
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def finish_agent_work(self, issue_id: str) -> Issue:
        """Finish agent work on an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")

            node_data = dict(record["i"])
            if not node_data.get("agentWorking", False):
                raise ValueError(f"Agent is not working on issue {issue_id}")

            update_result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates={
                    "agentWorking": False,
                    "agentFinishedAt": _now_iso(),
                },
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def get_agent_status(self, issue_id: str) -> dict[str, Any]:
        """Get agent work status for an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUE,
                id=issue_id,
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return {
                "agentWorking": record["i"].get("agentWorking", False),
                "agentStartedAt": record["i"].get("agentStartedAt"),
                "agentFinishedAt": record["i"].get("agentFinishedAt"),
                "agentId": record["i"].get("agentId"),
            }

    # -- Transactions ----------------------------------------------------------

    @contextmanager
    def transaction(self):  # type: ignore[misc]
        """Execute a block of operations as a logical unit.

        Note: Each repository method manages its own Neo4j session internally.
        This context manager exists to satisfy the TaskRepositoryInterface contract
        and to allow future refactoring toward explicit transaction passing.
        Currently behaves as a logical grouping marker (no-op yield).
        """
        yield

    def reset_data(self, scope: str = "all") -> dict[str, int]:
        """Reset data in the repository."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result: dict[str, int] = {}

            if scope in ("all", "issues"):
                res = session.run("MATCH (i:Issue) DETACH DELETE i RETURN count(*) as count")
                record = res.single()
                result["issues_deleted"] = record["count"] if record else 0

            if scope in ("all", "components"):
                res = session.run("MATCH (c:Component) DETACH DELETE c RETURN count(*) as count")
                record = res.single()
                result["components_deleted"] = record["count"] if record else 0

            return result

    # -- Label management --------------------------------------------------------

    def sync_labels_from_github(self, github_adapter) -> int:
        """Sync labels from GitHub repository."""
        from datetime import datetime, timezone
        from uuid import uuid4

        labels = github_adapter.list_labels() if github_adapter else []
        synced = 0

        with self._driver.driver.session(database=self._driver.database) as session:
            for label in labels:
                session.run(
                    queries.CREATE_LABEL,
                    id=str(uuid4()),
                    name=label.get("name", ""),
                    color=label.get("color", ""),
                    description=label.get("description", ""),
                    createdAt=datetime.now(timezone.utc).isoformat(),
                    updatedAt=datetime.now(timezone.utc).isoformat(),
                )
                synced += 1

        return synced

    def get_all_labels(self) -> list[dict]:
        """Get all labels from Neo4j."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ALL_LABELS)
            return [dict(r["l"]) for r in result]

    def link_issue_to_labels(self, issue_id: str, label_names: list[str]) -> None:
        """Link an issue to labels."""
        with self._driver.driver.session(database=self._driver.database) as session:
            for label_name in label_names:
                session.run(
                    queries.LINK_ISSUE_TO_LABEL,
                    issue_id=issue_id,
                    label_name=label_name,
                )

    def get_issues_by_labels(self, labels: list[str]) -> list[Issue]:
        """Get issues filtered by labels."""
        if not labels:
            return []

        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_ISSUES_BY_LABELS,
                labels=labels,
            )
            return [_node_to_issue(r["i"]) for r in result]

    # -- Constraints ----------------------------------------------------------

    def create_constraint(self, constraint: Constraint) -> None:
        """Persist a new constraint to Neo4j."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                """
                CREATE (c:Constraint {
                    id: $id,
                    category: $category,
                    level: $level,
                    pattern: $pattern,
                    service: $service,
                    target: $target,
                    from_layer: $from_layer,
                    to_layer: $to_layer,
                    rule_type: $rule_type,
                    max_depth: $max_depth,
                    required: $required,
                    description: $description,
                    status: $status,
                    createdAt: $createdAt,
                    updatedAt: $updatedAt
                })
                """,
                id=str(constraint.id),
                category=constraint.category.value,
                level=constraint.level.value,
                pattern=constraint.pattern,
                service=constraint.service,
                target=constraint.target,
                from_layer=constraint.from_layer,
                to_layer=constraint.to_layer,
                rule_type=constraint.rule_type,
                max_depth=constraint.max_depth,
                required=constraint.required,
                description=constraint.description,
                status=constraint.status.value,
                createdAt=constraint.created_at.isoformat(),
                updatedAt=constraint.updated_at.isoformat(),
            )

    def list_constraints(self, category: str | None = None) -> list[Constraint]:
        """List constraints from Neo4j, optionally filtered by category."""
        with self._driver.driver.session(database=self._driver.database) as session:
            if category:
                result = session.run(
                    "MATCH (c:Constraint {category: $category}) RETURN c",
                    category=category,
                )
            else:
                result = session.run("MATCH (c:Constraint) RETURN c")

            constraints = []
            for r in result:
                node = dict(r["c"])
                constraints.append(
                    Constraint(
                        id=node.get("id"),
                        category=ConstraintCategory(node.get("category", "architecture")),
                        level=ConstraintLevel(node.get("level", "hard")),
                        pattern=node.get("pattern", ""),
                        service=node.get("service", ""),
                        target=node.get("target", ""),
                        from_layer=node.get("from_layer", ""),
                        to_layer=node.get("to_layer", ""),
                        rule_type=node.get("rule_type", ""),
                        max_depth=node.get("max_depth"),
                        required=node.get("required", True),
                        description=node.get("description", ""),
                        status=ConstraintStatus(node.get("status", "inactive")),
                    )
                )
            return constraints

    def get_constraint(self, constraint_id: str) -> Constraint | None:
        """Retrieve a constraint by ID."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                "MATCH (c:Constraint {id: $id}) RETURN c",
                id=constraint_id,
            )
            record = result.single()
            if record is None:
                return None

            node = dict(record["c"])
            return Constraint(
                id=node.get("id"),
                category=ConstraintCategory(node.get("category", "architecture")),
                level=ConstraintLevel(node.get("level", "hard")),
                pattern=node.get("pattern", ""),
                service=node.get("service", ""),
                target=node.get("target", ""),
                from_layer=node.get("from_layer", ""),
                to_layer=node.get("to_layer", ""),
                rule_type=node.get("rule_type", ""),
                max_depth=node.get("max_depth"),
                required=node.get("required", True),
                description=node.get("description", ""),
                status=ConstraintStatus(node.get("status", "inactive")),
            )

    def delete_constraint(self, constraint_id: str) -> None:
        """Delete a constraint from Neo4j."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                "MATCH (c:Constraint {id: $id}) DETACH DELETE c",
                id=constraint_id,
            )

    def update_constraint(self, constraint_id: str, updates: dict) -> Constraint:
        """Update a constraint in Neo4j."""
        with self._driver.driver.session(database=self._driver.database) as session:
            set_clauses = []
            params = {"id": constraint_id}

            for key, value in updates.items():
                set_clauses.append(f"c.{key} = ${key}")
                params[key] = value

            set_clauses.append("c.updated_at = $updatedAt")
            params["updatedAt"] = datetime.now(timezone.utc).isoformat()

            query = f"MATCH (c:Constraint {{id: $id}}) SET {', '.join(set_clauses)} RETURN c"
            result = session.run(query, **params)
            record = result.single()

            if record is None:
                raise ValueError(f"Constraint {constraint_id} not found")

            return self.get_constraint(constraint_id)

    # ---------------------------------------------------------------------------
    # Epic methods
    # ---------------------------------------------------------------------------

    def create_epic(self, epic) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_EPIC,
                id=str(epic.id),
                name=epic.name,
                description=epic.description,
                objective_id=str(epic.objective_id) if epic.objective_id else None,
                status=epic.status.value,
                createdAt=epic.createdAt.isoformat(),
                updatedAt=epic.updatedAt.isoformat(),
            )

    def get_epic(self, epicId: str):
        from uuid import UUID

        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_EPIC, id=epicId)
            record = result.single()
            if record is None:
                return None
            node = record["e"]
            from socialseed_tasker.core.task_management.entities import Epic, EpicStatus

            return Epic(
                id=UUID(node["id"]),
                name=node["name"],
                description=node.get("description", ""),
                objective_id=UUID(node["objective_id"]) if node.get("objective_id") else None,
                status=EpicStatus(node.get("status", "OPEN")),
            )

    def list_epics(self):
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_EPICS)
            from uuid import UUID

            from socialseed_tasker.core.task_management.entities import Epic, EpicStatus

            epics = []
            for record in result:
                node = record["e"]
                epics.append(
                    Epic(
                        id=UUID(node["id"]),
                        name=node["name"],
                        description=node.get("description", ""),
                        objective_id=UUID(node["objective_id"]) if node.get("objective_id") else None,
                        status=EpicStatus(node.get("status", "OPEN")),
                    )
                )
            return epics

    def delete_epic(self, epicId: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_EPIC, id=epicId)

    def link_issue_to_epic(self, issue_id: str, epicId: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.LINK_ISSUE_TO_EPIC, issue_id=issue_id, epicId=epicId)

    def update_epic(self, epicId: str, updates: dict) -> None:
        from datetime import datetime, timezone

        with self._driver.driver.session(database=self._driver.database) as session:
            set_clauses = []
            params = {"id": epicId, "updatedAt": datetime.now(timezone.utc).isoformat()}

            for key, value in updates.items():
                set_clauses.append(f"e.{key} = ${key}")
                params[key] = value

            query = f"MATCH (e:Epic {{id: $id}}) SET {', '.join(set_clauses)} RETURN e"
            session.run(query, **params)

    # ---------------------------------------------------------------------------
    # Objective methods
    # ---------------------------------------------------------------------------

    def create_objective(self, objective) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_OBJECTIVE,
                id=str(objective.id),
                name=objective.name,
                description=objective.description,
                status=objective.status.value,
                quarter=objective.quarter,
                createdAt=objective.createdAt.isoformat(),
                updatedAt=objective.updatedAt.isoformat(),
            )

    def get_objective(self, objective_id: str):
        from uuid import UUID

        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_OBJECTIVE, id=objective_id)
            record = result.single()
            if record is None:
                return None
            node = record["o"]
            from socialseed_tasker.core.task_management.entities import Objective, ObjectiveStatus

            return Objective(
                id=UUID(node["id"]),
                name=node["name"],
                description=node.get("description", ""),
                status=ObjectiveStatus(node.get("status", "OPEN")),
                quarter=node.get("quarter", ""),
            )

    def list_objectives(self):
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_OBJECTIVES)
            from uuid import UUID

            from socialseed_tasker.core.task_management.entities import Objective, ObjectiveStatus

            objectives = []
            for record in result:
                node = record["o"]
                objectives.append(
                    Objective(
                        id=UUID(node["id"]),
                        name=node["name"],
                        description=node.get("description", ""),
                        status=ObjectiveStatus(node.get("status", "OPEN")),
                        quarter=node.get("quarter", ""),
                    )
                )
            return objectives

    def delete_objective(self, objective_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_OBJECTIVE, id=objective_id)

    def link_epic_to_objective(self, epicId: str, objective_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.LINK_EPIC_TO_OBJECTIVE, epicId=epicId, objective_id=objective_id)

    def update_objective(self, objective_id: str, updates: dict) -> None:
        from datetime import datetime, timezone

        with self._driver.driver.session(database=self._driver.database) as session:
            set_clauses = []
            params = {"id": objective_id, "updatedAt": datetime.now(timezone.utc).isoformat()}

            for key, value in updates.items():
                set_clauses.append(f"o.{key} = ${key}")
                params[key] = value

            query = f"MATCH (o:Objective {{id: $id}}) SET {', '.join(set_clauses)} RETURN o"
            session.run(query, **params)

    # ---------------------------------------------------------------------------
    # Cost Analytics methods
    # ---------------------------------------------------------------------------

    def get_cost_per_component(self) -> list[dict]:
        """Get cost breakdown by component for closed issues."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_COST_PER_COMPONENT)
            return [
                {
                    "componentId": record["componentId"],
                    "component_name": record["component_name"],
                    "actual_cost": record.get("actual_cost", 0.0) or 0.0,
                    "avg_hourly_rate": record.get("avg_hourly_rate", 0.0) or 0.0,
                    "total_hours": record.get("total_hours", 0) or 0,
                    "issue_count": record.get("issue_count", 0) or 0,
                }
                for record in result
            ]

    def get_cost_per_epic(self) -> list[dict]:
        """Get cost breakdown by epic for closed issues."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_COST_PER_EPIC)
            return [
                {
                    "epicId": record["epicId"],
                    "epic_name": record["epic_name"],
                    "actual_cost": record.get("actual_cost", 0.0) or 0.0,
                    "total_hours": record.get("total_hours", 0) or 0,
                    "issue_count": record.get("issue_count", 0) or 0,
                }
                for record in result
            ]

    def get_cost_per_project(self) -> list[dict]:
        """Get cost breakdown by project for closed issues."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_COST_PER_PROJECT)
            return [
                {
                    "projectId": record["projectId"],
                    "project_name": record["project_name"],
                    "actual_cost": record.get("actual_cost", 0.0) or 0.0,
                    "total_hours": record.get("total_hours", 0) or 0,
                    "issue_count": record.get("issue_count", 0) or 0,
                }
                for record in result
            ]

    def get_cost_summary(self) -> dict:
        """Get overall cost summary."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_COST_SUMMARY)
            record = result.single()
            if record is None:
                return {
                    "total_actual_cost": 0.0,
                    "total_hours": 0,
                    "total_issues_closed": 0,
                }
            return {
                "total_actual_cost": record.get("total_actual_cost", 0.0) or 0.0,
                "total_hours": record.get("total_hours", 0) or 0,
                "total_issues_closed": record.get("total_issues_closed", 0) or 0,
            }

    # ---------------------------------------------------------------------------
    # Deployment methods
    # ---------------------------------------------------------------------------

    def create_deployment(self, deployment) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_DEPLOYMENT,
                id=str(deployment.id),
                commit_sha=deployment.commit_sha,
                environment_name=deployment.environment_name.value,
                deployed_at=deployment.deployed_at.isoformat(),
                issue_ids=[str(i) for i in deployment.issue_ids],
                channel=deployment.channel,
                deployed_by=deployment.deployed_by,
            )

    def get_deployments(
        self,
        environment_name: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.GET_DEPLOYMENTS,
                environment_name=environment_name,
                limit=limit,
            )
            return [
                {
                    "id": record["d"]["id"],
                    "commit_sha": record["d"]["commit_sha"],
                    "environment_name": record["d"]["environment_name"],
                    "deployed_at": record["d"]["deployed_at"],
                    "issue_ids": record["d"].get("issue_ids", []),
                    "channel": record["d"].get("channel"),
                    "deployed_by": record["d"].get("deployed_by"),
                }
                for record in result
            ]

    def get_deployment_by_commit(self, commit_sha: str) -> dict | None:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_DEPLOYMENT_BY_COMMIT, commit_sha=commit_sha)
            record = result.single()
            if record is None:
                return None
            return {
                "id": record["d"]["id"],
                "commit_sha": record["d"]["commit_sha"],
                "environment_name": record["d"]["environment_name"],
                "deployed_at": record["d"]["deployed_at"],
                "issue_ids": record["d"].get("issue_ids", []),
            }

    def get_issue_deployments(self, issue_id: str) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUES_DEPLOYMENTS, issue_id=issue_id)
            return [
                {
                    "id": record["d"]["id"],
                    "commit_sha": record["d"]["commit_sha"],
                    "environment_name": record["d"]["environment_name"],
                    "deployed_at": record["d"]["deployed_at"],
                    "channel": record["d"].get("channel"),
                }
                for record in result
            ]

    # ---------------------------------------------------------------------------
    # Vector Search methods
    # ---------------------------------------------------------------------------

    def search_by_embedding(self, embedding: list[float], threshold: float = 0.7, limit: int = 10) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.SEARCH_BY_EMBEDDING,
                embedding=embedding,
                threshold=threshold,
                limit=limit,
            )
            return [
                {
                    "issue_id": record["issue_id"],
                    "title": record["title"],
                    "score": record["score"],
                }
                for record in result
            ]

    def find_similar_issues(self, issue_id: str, threshold: float = 0.7, limit: int = 10) -> list[dict]:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.FIND_SIMILAR_ISSUES,
                issue_id=issue_id,
                threshold=threshold,
                limit=limit,
            )
            return [
                {
                    "issue_id": record["issue_id"],
                    "title": record["title"],
                    "score": record["score"],
                }
                for record in result
            ]

    def update_issue_embedding(self, issue_id: str, embedding: list[float]) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.UPDATE_ISSUE_EMBEDDING,
                id=issue_id,
                embedding=embedding,
            )