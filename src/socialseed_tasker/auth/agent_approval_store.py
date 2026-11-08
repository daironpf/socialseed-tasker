"""PostgreSQL persistence for human approvals (issue #616)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from contextlib import closing
from datetime import datetime
from typing import Any

import psycopg

from socialseed_tasker.domain.agent_approval import (
    APPROVAL_APPROVED,
    APPROVAL_EXPIRED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    APPROVAL_REVOKED,
)

AGENT_APPROVALS_DDL = """
CREATE TABLE IF NOT EXISTS agent_approvals (
    id                 TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    run_id             TEXT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    agent_id           TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issue_id           TEXT NOT NULL,
    project_id         TEXT NOT NULL,
    action             TEXT NOT NULL,
    tool               TEXT,
    resource_scope     TEXT NOT NULL,
    target             TEXT,
    expected_effect    TEXT NOT NULL,
    action_payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    action_fingerprint TEXT NOT NULL,
    request_metadata   JSONB NOT NULL DEFAULT '{}'::jsonb,
    status             TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending','approved','rejected','revoked','expired')
    ),
    requested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at         TIMESTAMPTZ,
    decided_at         TIMESTAMPTZ,
    decided_by         TEXT,
    feedback           TEXT,
    revoked_at         TIMESTAMPTZ,
    revoked_by         TEXT,
    executed_at        TIMESTAMPTZ
)
"""

AGENT_APPROVALS_INDEX_DDL: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS ix_agent_approvals_status_requested ON agent_approvals (status, requested_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_agent_approvals_run ON agent_approvals (run_id)",
    "CREATE INDEX IF NOT EXISTS ix_agent_approvals_agent_requested ON agent_approvals (agent_id, requested_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_agent_approvals_issue_status ON agent_approvals (issue_id, status)",
)

_APPROVAL_ROW_SQL = (
    "id, run_id, agent_id, issue_id, project_id, action, tool, resource_scope, "
    "target, expected_effect, action_payload, action_fingerprint, request_metadata, "
    "status, requested_at, expires_at, decided_at, decided_by, feedback, "
    "revoked_at, revoked_by, executed_at"
)


def _as_json_dict(value: Any) -> dict[str, Any]:
    """Normalize psycopg JSONB values (dict or legacy string) to a dict."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    return {}


class PostgresAgentApprovalStore:
    """CRUD and atomic transitions over ``agent_approvals``."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    @staticmethod
    def _row(row: tuple[Any, ...]) -> dict[str, Any]:
        result = {
            "id": row[0],
            "run_id": row[1],
            "agent_id": row[2],
            "issue_id": row[3],
            "project_id": row[4],
            "action": row[5],
            "tool": row[6],
            "resource_scope": row[7],
            "target": row[8],
            "expected_effect": row[9],
            "action_payload": _as_json_dict(row[10]),
            "action_fingerprint": row[11],
            "request_metadata": _as_json_dict(row[12]),
            "status": row[13],
            "requested_at": row[14],
            "expires_at": row[15],
            "decided_at": row[16],
            "decided_by": row[17],
            "feedback": row[18],
            "revoked_at": row[19],
            "revoked_by": row[20],
            "executed_at": row[21],
        }
        return result

    def create_approval(self, **fields: Any) -> dict[str, Any]:
        """Insert a pending request and return the stored row."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_approvals (
                    run_id, agent_id, issue_id, project_id, action, tool,
                    resource_scope, target, expected_effect, action_payload,
                    action_fingerprint, request_metadata, status, requested_at,
                    expires_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s::jsonb, %s, %s, %s
                ) RETURNING """
                + _APPROVAL_ROW_SQL,
                (
                    fields["run_id"],
                    fields["agent_id"],
                    fields["issue_id"],
                    fields["project_id"],
                    fields["action"],
                    fields.get("tool"),
                    fields["resource_scope"],
                    fields.get("target"),
                    fields["expected_effect"],
                    json.dumps(fields.get("action_payload") or {}),
                    fields["action_fingerprint"],
                    json.dumps(fields.get("request_metadata") or {}),
                    fields.get("status") or APPROVAL_PENDING,
                    fields["requested_at"],
                    fields.get("expires_at"),
                ),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("agent_approvals INSERT RETURNING produced no row")
            return self._row(row)

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        """Return one approval by id."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT {_APPROVAL_ROW_SQL} FROM agent_approvals WHERE id = %s",
                (approval_id,),
            )
            row = cur.fetchone()
            return self._row(row) if row is not None else None

    def list_approvals(
        self,
        *,
        status: str | None = None,
        issue_id: str | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List approvals newest-first, optionally filtered."""
        where: list[str] = []
        params: list[Any] = []
        if status is not None:
            where.append("status = %s")
            params.append(status)
        if issue_id is not None:
            where.append("issue_id = %s")
            params.append(issue_id)
        if agent_id is not None:
            where.append("agent_id = %s")
            params.append(agent_id)
        if project_id is not None:
            where.append("project_id = %s")
            params.append(project_id)
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT {_APPROVAL_ROW_SQL} FROM agent_approvals{where_sql} "
                "ORDER BY requested_at DESC, id DESC LIMIT %s",
                (*params, limit),
            )
            return [self._row(row) for row in cur.fetchall()]

    def expire_due(self, now: datetime) -> int:
        """Materialize expired pending/approved requests; returns rows changed."""
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE agent_approvals
                SET status = %s,
                    decided_at = COALESCE(decided_at, %s),
                    feedback = COALESCE(feedback, %s)
                WHERE status IN (%s, %s)
                  AND executed_at IS NULL
                  AND expires_at IS NOT NULL
                  AND expires_at <= %s
                """,
                (
                    APPROVAL_EXPIRED,
                    now,
                    "approval expired before execution",
                    APPROVAL_PENDING,
                    APPROVAL_APPROVED,
                    now,
                ),
            )
            return int(cur.rowcount or 0)

    def transition_approval(
        self,
        approval_id: str,
        *,
        from_statuses: Sequence[str],
        status: str,
        actor_id: str | None,
        feedback: str | None,
        now: datetime,
    ) -> dict[str, Any] | None:
        """Atomically move one approval between states.

        ``None`` means another writer won the race or the expected state no
        longer holds; callers must reload and report a conflict.
        """
        if status == APPROVAL_REVOKED:
            assignment = "status = %s, revoked_at = %s, revoked_by = %s, feedback = COALESCE(%s, feedback)"
            values: tuple[Any, ...] = (status, now, actor_id, feedback)
        elif status in {APPROVAL_APPROVED, APPROVAL_REJECTED}:
            assignment = "status = %s, decided_at = %s, decided_by = %s, feedback = %s"
            values = (status, now, actor_id, feedback)
        else:
            raise ValueError(f"unsupported approval transition: {status}")

        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                f"UPDATE agent_approvals SET {assignment} "
                "WHERE id = %s AND status = ANY(%s) AND executed_at IS NULL "
                f"RETURNING {_APPROVAL_ROW_SQL}",
                (*values, approval_id, list(from_statuses)),
            )
            row = cur.fetchone()
            return self._row(row) if row is not None else None

    def consume_approval(
        self,
        approval_id: str,
        *,
        action_fingerprint: str,
        now: datetime,
    ) -> dict[str, Any] | None:
        """Mark an approved request as executed exactly once.

        The update rechecks status, deadline and fingerprint in the same SQL
        statement, so concurrent executors cannot both consume the approval.
        """
        with closing(psycopg.connect(self._database_url, autocommit=True)) as conn, conn.cursor() as cur:
            cur.execute(
                f"UPDATE agent_approvals SET executed_at = %s "
                "WHERE id = %s AND status = %s AND executed_at IS NULL "
                "AND action_fingerprint = %s "
                "AND (expires_at IS NULL OR expires_at > %s) "
                f"RETURNING {_APPROVAL_ROW_SQL}",
                (now, approval_id, APPROVAL_APPROVED, action_fingerprint, now),
            )
            row = cur.fetchone()
            return self._row(row) if row is not None else None
