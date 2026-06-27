"""User Repository - Neo4j storage for User entities.

Provides CRUD operations and relationship management for users.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from socialseed_tasker.domain.entities import User, UserRole
from socialseed_tasker.infrastructure import neo4j_queries as queries


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _node_to_user(node: dict[str, Any]) -> User:
    """Convert a Neo4j node to a domain User."""
    return User(
        id=UUID(node["id"]),
        username=node["username"],
        email=node.get("email"),
        role=UserRole(node.get("role", "developer")),
        github_handle=node.get("githubHandle") or node.get("github_handle"),
        created_at=datetime.fromisoformat(node.get("createdAt") or node.get("created_at", datetime.now(timezone.utc).isoformat())),
        last_login=datetime.fromisoformat(node.get("lastLogin") or node.get("last_login")) if node.get("lastLogin") or node.get("last_login") else None,
        preferences=node.get("preferences"),
    )


class UserRepository:
    """Repository for User entities in Neo4j."""

    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def _get_session(self):
        """Get Neo4j session."""
        if hasattr(self._driver, "driver"):
            return self._driver.driver.session(database=self._driver.database)
        return self._driver.session(database="neo4j")

    def create_user(self, user: User) -> None:
        """Create a new User node in Neo4j."""
        with self._get_session() as session:
            session.run(
                queries.CREATE_USER,
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role.value,
                github_handle=user.github_handle,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None,
                preferences=user.preferences,
            )

    def get_user(self, user_id: str) -> User | None:
        """Get a user by ID."""
        with self._get_session() as session:
            result = session.run(queries.GET_USER, id=user_id)
            record = result.single()
            return _node_to_user(record["u"]) if record else None

    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
        with self._get_session() as session:
            result = session.run(queries.GET_USER_BY_EMAIL, email=email)
            record = result.single()
            return _node_to_user(record["u"]) if record else None

    def get_user_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        with self._get_session() as session:
            result = session.run(queries.GET_USER_BY_USERNAME, username=username)
            record = result.single()
            return _node_to_user(record["u"]) if record else None

    def update_user(self, user_id: str, updates: dict[str, Any]) -> User:
        """Update user properties."""
        with self._get_session() as session:
            result = session.run(
                queries.UPDATE_USER,
                id=user_id,
                updates=updates,
                updated_at=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"User {user_id} not found")
            return _node_to_user(record["u"])

    def delete_user(self, user_id: str) -> None:
        """Delete a user from Neo4j."""
        with self._get_session() as session:
            session.run(queries.DELETE_USER, id=user_id)

    def list_users(self, role: str | None = None, limit: int = 50) -> list[User]:
        """List users, optionally filtered by role."""
        with self._get_session() as session:
            result = session.run(queries.LIST_USERS, role=role, limit=limit)
            return [_node_to_user(r["u"]) for r in result]

    def update_last_login(self, user_id: str) -> None:
        """Update the last login timestamp."""
        with self._get_session() as session:
            session.run(
                queries.UPDATE_LAST_LOGIN,
                id=user_id,
                last_login=_now_iso(),
            )

    def link_user_to_project(self, user_id: str, project_id: str) -> None:
        """Create (User)-[:MANAGES]->(Project) relationship."""
        with self._get_session() as session:
            session.run(
                queries.USER_MANAGES_PROJECT,
                user_id=user_id,
                project_id=project_id,
            )

    def link_user_to_reasoning(
        self, user_id: str, reasoning_id: str, approved: bool, comment: str
    ) -> None:
        """Create (User)-[:VALIDATES {approved, comment}]->(ReasoningNode) relationship."""
        with self._get_session() as session:
            session.run(
                queries.USER_VALIDATES_REASONING,
                user_id=user_id,
                reasoning_id=reasoning_id,
                approved=approved,
                comment=comment,
            )

    def link_user_to_issue(self, user_id: str, issue_id: str) -> None:
        """Create (User)-[:ASSIGNED_TO]->(Issue) relationship."""
        with self._get_session() as session:
            session.run(
                queries.USER_ASSIGNED_TO_ISSUE,
                user_id=user_id,
                issue_id=issue_id,
            )

    def link_user_to_commit(self, user_id: str, commit_sha: str) -> None:
        """Create (User)-[:AUTHORED]->(Commit) relationship."""
        with self._get_session() as session:
            session.run(
                queries.USER_AUTHORED_COMMIT,
                user_id=user_id,
                commit_sha=commit_sha,
            )

    def get_user_projects(self, user_id: str) -> list[dict[str, Any]]:
        """Get all projects managed by a user."""
        with self._get_session() as session:
            result = session.run(queries.GET_USER_PROJECTS, user_id=user_id)
            return [dict(r["p"]) for r in result]

    def get_user_issues(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get all issues assigned to a user."""
        with self._get_session() as session:
            result = session.run(queries.GET_USER_ISSUES, user_id=user_id, limit=limit)
            return [dict(r["i"]) for r in result]

    def get_user_commits(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get all commits authored by a user."""
        with self._get_session() as session:
            result = session.run(queries.GET_USER_COMMITS, user_id=user_id, limit=limit)
            return [dict(r["c"]) for r in result]