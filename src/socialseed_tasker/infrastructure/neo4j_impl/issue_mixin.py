from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from socialseed_tasker.domain.entities import Issue
from socialseed_tasker.infrastructure.embedding_service import get_embedding_service
from socialseed_tasker.infrastructure import neo4j_queries as queries
from socialseed_tasker.infrastructure.neo4j_impl.shared import _node_to_issue, _now_iso, _to_uuid_list, _to_camel


class IssueRepositoryMixin:
    """Issue CRUD and related operations."""

    def create_issue(self, issue: Issue) -> Issue:
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
                reasoningLogs=json.dumps(reasoning_logs_data),
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
        return issue

    def get_issue(self, issue_id: str) -> Issue | None:
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUE, id=issue_id)
            record = result.single()
            if record is None:
                return None
            return _node_to_issue(record["i"])

    def update_issue(self, issue_id: str, updates: dict[str, Any]) -> Issue:
        with self._driver.driver.session(database=self._driver.database) as session:
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

            # Create (Issue)-[:RESOLVED_BY]->(Commit) if commit_sha provided
            if commit_sha:
                try:
                    session.run(
                        queries.LINK_COMMIT_TO_ISSUE,
                        sha=commit_sha,
                        issue_id=issue_id,
                    )
                except Exception:
                    pass

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
                dep_ids = _to_uuid_list(r.get("dep_ids"))
                blocked_ids = _to_uuid_list(r.get("blocked_ids"))
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
                cypher += " AND i.componentId = $component_id"
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
            existing_logs_raw = node_data.get("reasoningLogs", [])
            existing_logs = json.loads(existing_logs_raw) if isinstance(existing_logs_raw, str) else (existing_logs_raw or [])
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
                updates={"reasoningLogs": json.dumps(existing_logs)},
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
            raw = record["i"].get("reasoningLogs", [])
            if isinstance(raw, str):
                raw = json.loads(raw)
            return raw

    # -- Comments ----------------------------------------------------------------

    def add_comment(self, issue_id: str, text: str, author: str = "api-user") -> Issue:
        """Add a comment to an issue and return the updated issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUE, id=issue_id)
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")

            node_data = dict(record["i"])
            existing_raw = node_data.get("comments", [])
            existing = json.loads(existing_raw) if isinstance(existing_raw, str) else (existing_raw or [])
            new_entry = {
                "id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "author": author,
                "text": text,
            }
            existing.append(new_entry)

            update_result = session.run(
                queries.UPDATE_ISSUE,
                id=issue_id,
                updates={"comments": json.dumps(existing)},
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def get_comments(self, issue_id: str) -> list[dict[str, Any]]:
        """Get all comments for an issue."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_ISSUE, id=issue_id)
            record = result.single()
            if record is None:
                raise ValueError(f"Issue {issue_id} not found")
            raw = record["i"].get("comments", [])
            if isinstance(raw, str):
                raw = json.loads(raw)
            return raw

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
                    "agentId": agent_id,
                },
                updatedAt=_now_iso(),
            )
            updated_record = update_result.single()
            if updated_record is None:
                raise ValueError(f"Issue {issue_id} not found")
            return _node_to_issue(updated_record["i"])

    def finish_agent_work(self, issue_id: str, agent_id: str) -> Issue:
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
                    "agentFinishedBy": agent_id,
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
