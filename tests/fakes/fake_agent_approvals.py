"""In-memory ``AgentApprovalStore`` for lifecycle and API tests (issue #616)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from socialseed_tasker.domain.agent_approval import (
    APPROVAL_APPROVED,
    APPROVAL_EXPIRED,
    APPROVAL_PENDING,
)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class FakeAgentApprovalStore:
    """Stateful store with the same atomic transition contract as PostgreSQL."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self._sequence = 0

    def _next_id(self) -> str:
        self._sequence += 1
        return f"approval-{self._sequence}"

    def _copy(self, row: dict[str, Any]) -> dict[str, Any]:
        return dict(row)

    def create_approval(self, **fields: Any) -> dict[str, Any]:
        approval_id = self._next_id()
        row = {
            "id": approval_id,
            "decided_at": None,
            "decided_by": None,
            "feedback": None,
            "revoked_at": None,
            "revoked_by": None,
            "executed_at": None,
            **fields,
        }
        self.rows[approval_id] = row
        return self._copy(row)

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        row = self.rows.get(approval_id)
        return self._copy(row) if row is not None else None

    def list_approvals(
        self,
        *,
        status: str | None = None,
        issue_id: str | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = list(self.rows.values())
        filters = {
            "status": status,
            "issue_id": issue_id,
            "agent_id": agent_id,
            "project_id": project_id,
        }
        rows = [row for row in rows if all(value is None or row.get(key) == value for key, value in filters.items())]
        rows.sort(key=lambda row: row.get("requested_at") or datetime.min, reverse=True)
        return [self._copy(row) for row in rows[:limit]]

    def expire_due(self, now: datetime) -> int:
        changed = 0
        for row in self.rows.values():
            if row["status"] not in {APPROVAL_PENDING, APPROVAL_APPROVED}:
                continue
            if row.get("executed_at") is not None:
                continue
            expires_at = _as_utc(row.get("expires_at"))
            if expires_at is not None and expires_at <= now:
                row["status"] = APPROVAL_EXPIRED
                row["decided_at"] = row.get("decided_at") or now
                row["feedback"] = row.get("feedback") or "approval expired before execution"
                changed += 1
        return changed

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
        row = self.rows.get(approval_id)
        if row is None or row["status"] not in from_statuses or row.get("executed_at") is not None:
            return None
        row["status"] = status
        if status == "revoked":
            row["revoked_at"] = now
            row["revoked_by"] = actor_id
            if feedback is not None:
                row["feedback"] = feedback
        else:
            row["decided_at"] = now
            row["decided_by"] = actor_id
            row["feedback"] = feedback
        return self._copy(row)

    def consume_approval(
        self,
        approval_id: str,
        *,
        action_fingerprint: str,
        now: datetime,
    ) -> dict[str, Any] | None:
        row = self.rows.get(approval_id)
        if (
            row is None
            or row["status"] != APPROVAL_APPROVED
            or row.get("executed_at") is not None
            or row.get("action_fingerprint") != action_fingerprint
        ):
            return None
        expires_at = _as_utc(row.get("expires_at"))
        if expires_at is not None and expires_at <= now:
            return None
        row["executed_at"] = now
        return self._copy(row)
