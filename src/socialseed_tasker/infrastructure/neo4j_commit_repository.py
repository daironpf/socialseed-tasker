"""Commit Repository - Neo4j storage for Commit entities.

Provides CRUD operations and relationship management for commits.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from socialseed_tasker.core.task_management.entities import Commit
from socialseed_tasker.storage.graph_database import queries


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _node_to_commit(node: dict[str, Any]) -> Commit:
    """Convert a Neo4j node to a domain Commit."""
    return Commit(
        sha=node["sha"],
        message=node.get("message", ""),
        author_name=node.get("authorName") or node.get("author_name", ""),
        author_email=node.get("authorEmail") or node.get("author_email", ""),
        timestamp=datetime.fromisoformat(node.get("timestamp")) if node.get("timestamp") else datetime.now(timezone.utc),
        is_ai_generated=node.get("isAiGenerated") or node.get("is_ai_generated", False),
        branch=node.get("branch", ""),
        additions=node.get("additions", 0),
        deletions=node.get("deletions", 0),
        files_changed=node.get("filesChanged") or node.get("files_changed", 0),
    )


class CommitRepository:
    """Repository for Commit entities in Neo4j."""

    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def _get_session(self):
        """Get Neo4j session."""
        if hasattr(self._driver, "driver"):
            return self._driver.driver.session(database=self._driver.database)
        return self._driver.session(database="neo4j")

    def create_commit(self, commit: Commit) -> None:
        """Create a new Commit node in Neo4j."""
        with self._get_session() as session:
            session.run(
                queries.CREATE_COMMIT,
                sha=commit.sha,
                message=commit.message,
                author_name=commit.authorName,
                author_email=commit.authorEmail,
                timestamp=commit.timestamp.isoformat(),
                is_ai_generated=commit.isAiGenerated,
                branch=commit.branch,
                additions=commit.additions,
                deletions=commit.deletions,
                files_changed=commit.filesChanged,
            )

    def get_commit(self, sha: str) -> Commit | None:
        """Get a commit by SHA hash."""
        with self._get_session() as session:
            result = session.run(queries.GET_COMMIT, sha=sha)
            record = result.single()
            return _node_to_commit(record["c"]) if record else None

    def list_commits(
        self,
        branch: str | None = None,
        author: str | None = None,
        is_ai_generated: bool | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Commit]:
        """List commits with optional filters."""
        with self._get_session() as session:
            result = session.run(
                queries.LIST_COMMITS,
                branch=branch,
                author=author,
                is_ai_generated=is_ai_generated,
                since=since.isoformat() if since else None,
                until=until.isoformat() if until else None,
                limit=limit,
                skip=skip,
            )
            return [_node_to_commit(r["c"]) for r in result]

    def delete_commit(self, sha: str) -> None:
        """Delete a commit from Neo4j."""
        with self._get_session() as session:
            session.run(queries.DELETE_COMMIT, sha=sha)

    def link_commit_to_agent(self, sha: str, agent_id: str) -> None:
        """Create (Agent)-[:AUTHORED]->(Commit) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_COMMIT_TO_AGENT,
                sha=sha,
                agent_id=agent_id,
            )

    def link_commit_to_user(self, sha: str, user_id: str) -> None:
        """Create (User)-[:AUTHORED]->(Commit) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_COMMIT_TO_USER,
                sha=sha,
                user_id=user_id,
            )

    def link_commit_to_issue(self, sha: str, issue_id: str) -> None:
        """Create (Issue)-[:RESOLVED_BY]->(Commit) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_COMMIT_TO_ISSUE,
                sha=sha,
                issue_id=issue_id,
            )

    def link_commit_to_file(self, sha: str, file_path: str, change_type: str) -> None:
        """Create (Commit)-[:MODIFIED {type: "ADDED"|"MODIFIED"|"DELETED"}]->(CodeFile) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_COMMIT_TO_FILE,
                sha=sha,
                file_path=file_path,
                change_type=change_type,
            )

    def link_commit_to_reasoning(self, sha: str, reasoning_id: str) -> None:
        """Create (ReasoningNode)-[:RESULTED_IN]->(Commit) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_COMMIT_TO_REASONING,
                sha=sha,
                reasoning_id=reasoning_id,
            )

    def get_commits_for_issue(self, issue_id: str, limit: int = 50) -> list[Commit]:
        """Get all commits that resolved an issue."""
        with self._get_session() as session:
            result = session.run(queries.GET_COMMITS_FOR_ISSUE, issue_id=issue_id, limit=limit)
            return [_node_to_commit(r["c"]) for r in result]

    def get_commits_for_file(self, file_path: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get commit history for a file."""
        with self._get_session() as session:
            result = session.run(queries.GET_COMMITS_FOR_FILE, file_path=file_path, limit=limit)
            return [
                {"commit": _node_to_commit(r["c"]), "change_type": r["change_type"]}
                for r in result
            ]

    def get_commits_for_reasoning(self, reasoning_id: str, limit: int = 20) -> list[Commit]:
        """Get all commits that resulted from a reasoning."""
        with self._get_session() as session:
            result = session.run(queries.GET_COMMITS_FOR_REASONING, reasoning_id=reasoning_id, limit=limit)
            return [_node_to_commit(r["c"]) for r in result]

    def get_author_stats(self, since: datetime | None = None) -> dict[str, Any]:
        """Get commit statistics by author (human vs AI)."""
        with self._get_session() as session:
            result = session.run(
                queries.GET_AUTHOR_STATS,
                since=since.isoformat() if since else None,
            )
            record = result.single()
            if record:
                return {
                    "total_commits": record["total_commits"],
                    "total_additions": record["total_additions"],
                    "total_deletions": record["total_deletions"],
                    "total_files": record["total_files"],
                    "ai_authors": [a for a in record["ai_authors"] if a],
                    "human_authors": [u for u in record["human_authors"] if u],
                    "ai_commits": record["ai_commits"],
                    "human_commits": record["human_commits"],
                }
            return {
                "total_commits": 0,
                "total_additions": 0,
                "total_deletions": 0,
                "total_files": 0,
                "ai_authors": [],
                "human_authors": [],
                "ai_commits": 0,
                "human_commits": 0,
            }