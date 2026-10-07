"""Read repository over the normalized PostgreSQL user model (issue #558).

PostgreSQL is the root of users: ``GET /users`` composes each profile from
``users`` joined with ``human_user``/``agents_user`` and ``user_skills``/``skills``,
deriving ``last_login`` from ``session_logs`` and the response ``role`` from
``roles.id`` for humans (agents fall back to the derived ``ai-agent`` alias).
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import closing
from typing import Any

import psycopg

AGENT_ROLE_ALIAS = "ai-agent"

_LIST_HEAD = """
SELECT u.id, u.username, u.user_type, u.created_at,
       h.email, h.role_id, h.avatar, h.github_handle, h.preferences, h.is_active,
       a.email, a.avatar, a.model, a.specialization, a.enabled,
       (SELECT MAX(s.created_at) FROM session_logs s
         WHERE s.user_id = u.id AND s.event = 'login') AS last_login,
       COALESCE(array_agg(sk.name ORDER BY sk.name) FILTER (WHERE sk.id IS NOT NULL), '{}') AS skills
FROM users u
LEFT JOIN human_user h ON h.user_id = u.id
LEFT JOIN agents_user a ON a.user_id = u.id
LEFT JOIN user_skills us ON us.user_id = u.id
LEFT JOIN skills sk ON sk.id = us.skill_id
"""

_LIST_TAIL = """
GROUP BY u.id, h.user_id, a.user_id
ORDER BY u.username
LIMIT %s
"""

_ROLE_FILTER = (
    "COALESCE(CASE WHEN u.user_type = 'agent' THEN 'ai-agent' ELSE h.role_id END, 'DEVELOPER') = %s"
)


def _row_to_profile(row: Sequence[Any]) -> dict[str, Any]:
    """Map a composed JOIN row onto the API profile dictionary."""
    (
        user_id,
        username,
        user_type,
        created_at,
        human_email,
        role_id,
        human_avatar,
        github_handle,
        preferences,
        is_active,
        agent_email,
        agent_avatar,
        model,
        specialization,
        enabled,
        last_login,
        skills,
    ) = row
    skill_list = list(skills or [])
    if user_type == "agent":
        return {
            "id": user_id,
            "username": username,
            "type": "agent",
            "email": agent_email,
            "role": AGENT_ROLE_ALIAS,
            "avatar": agent_avatar,
            "skills": skill_list,
            "model": model,
            "specialization": specialization,
            "is_active": bool(enabled) if enabled is not None else True,
            "github_handle": None,
            "preferences": None,
            "created_at": created_at,
            "last_login": last_login,
        }
    return {
        "id": user_id,
        "username": username,
        "type": "human",
        "email": human_email,
        "role": role_id or "DEVELOPER",
        "avatar": human_avatar,
        "skills": skill_list,
        "model": None,
        "specialization": None,
        "is_active": bool(is_active) if is_active is not None else True,
        "github_handle": github_handle,
        "preferences": preferences,
        "created_at": created_at,
        "last_login": last_login,
    }


class PgUserRepository:
    """PostgreSQL user profile repository (list/get by id/email, identity, delete)."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def _fetch(self, where: str, params: Sequence[Any], limit: int) -> list[dict[str, Any]]:
        sql = _LIST_HEAD + " WHERE " + where + _LIST_TAIL
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(sql, (*params, limit))
            return [_row_to_profile(tuple(row)) for row in cur.fetchall()]

    def list_users(self, role: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Return composed profiles ordered by username, optionally filtered by response role."""
        if role:
            return self._fetch(_ROLE_FILTER, (role,), limit)
        return self._fetch("TRUE", (), limit)

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Return one profile by canonical uid, or ``None``."""
        rows = self._fetch("u.id = %s", (user_id,), limit=1)
        return rows[0] if rows else None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Return one profile by human or agent email, or ``None``."""
        rows = self._fetch("(h.email = %s OR a.email = %s)", (email, email), limit=1)
        return rows[0] if rows else None

    def list_identity(self) -> list[tuple[str, str]]:
        """Return ``(username, uid)`` pairs to re-key the Neo4j ``(:User)`` projection (#558)."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("SELECT username, id FROM users ORDER BY username")
            return [(str(row[0]), str(row[1])) for row in cur.fetchall()]

    def delete_user_row(self, user_id: str) -> bool:
        """Delete the identity row (profiles cascade); ``True`` when a row was removed."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return bool(cur.rowcount)
