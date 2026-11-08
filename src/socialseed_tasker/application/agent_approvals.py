"""Application service for human approvals of concrete agent actions (#616).

Persistence is delegated to an ``AgentApprovalStore``. The service owns the
state machine, the deadline semantics and the non-reusable execution check so
every transport (HTTP API, MCP or a future executor) applies the same rules.
"""

from __future__ import annotations

import hmac
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from typing import Any, Protocol

from socialseed_tasker.domain.agent_approval import (
    AGENT_APPROVAL_ACTIONS,
    AGENT_APPROVAL_STATUSES,
    APPROVAL_APPROVED,
    APPROVAL_EXPIRED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    APPROVAL_REVOKED,
    action_fingerprint,
    as_utc,
    effective_approval_status,
    utcnow,
)
from socialseed_tasker.domain.agent_permissions import AGENT_RESOURCE_SCOPES

_RESOURCE_SCOPE_SET = frozenset(AGENT_RESOURCE_SCOPES)


class AgentApprovalStore(Protocol):
    """Persistence contract used by :class:`AgentApprovalService`."""

    def create_approval(self, **fields: Any) -> dict[str, Any]: ...

    def get_approval(self, approval_id: str) -> dict[str, Any] | None: ...

    def list_approvals(
        self,
        *,
        status: str | None = None,
        issue_id: str | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def expire_due(self, now: datetime) -> int: ...

    def transition_approval(
        self,
        approval_id: str,
        *,
        from_statuses: Sequence[str],
        status: str,
        actor_id: str | None,
        feedback: str | None,
        now: datetime,
    ) -> dict[str, Any] | None: ...

    def consume_approval(
        self,
        approval_id: str,
        *,
        action_fingerprint: str,
        now: datetime,
    ) -> dict[str, Any] | None: ...


class AgentApprovalError(Exception):
    """A rejected approval transition or execution attempt."""

    def __init__(self, code: str, message: str, *, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class AgentApprovalService:
    """Enforce approval state transitions and one-shot execution."""

    def __init__(
        self,
        store: AgentApprovalStore,
        *,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._store = store
        self._clock = clock

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def list_approvals(
        self,
        *,
        status: str | None = None,
        issue_id: str | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return persisted approvals after materializing overdue deadlines."""
        if status is not None and status not in AGENT_APPROVAL_STATUSES:
            raise AgentApprovalError("unknown_status", "unknown approval status", status_code=422)
        self._store.expire_due(self._now())
        return self._store.list_approvals(
            status=status,
            issue_id=issue_id,
            agent_id=agent_id,
            project_id=project_id,
            limit=limit,
        )

    def get_approval(self, approval_id: str) -> dict[str, Any]:
        """Return one approval after materializing its deadline."""
        now = self._now()
        self._store.expire_due(now)
        row = self._require(approval_id)
        return self._with_effective_status(row, now)

    # ------------------------------------------------------------------
    # Request creation
    # ------------------------------------------------------------------
    def request_approval(
        self,
        *,
        run_id: str,
        agent_id: str,
        issue_id: str,
        project_id: str,
        action: str,
        tool: str | None,
        resource_scope: str,
        target: str | None,
        expected_effect: str,
        action_payload: dict[str, Any] | None,
        expires_in_seconds: int | None,
        request_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Persist a pending request bound to one run, action and effect."""
        if action not in AGENT_APPROVAL_ACTIONS:
            raise AgentApprovalError("unknown_action", "unknown agent action", status_code=422)
        if resource_scope not in _RESOURCE_SCOPE_SET:
            raise AgentApprovalError("unknown_resource_scope", "unknown resource scope", status_code=422)
        if not expected_effect.strip():
            raise AgentApprovalError("missing_expected_effect", "expected_effect is required", status_code=422)
        if expires_in_seconds is not None and expires_in_seconds <= 0:
            raise AgentApprovalError("invalid_expiry", "expires_in_seconds must be positive", status_code=422)

        now = self._now()
        expires_at = now + timedelta(seconds=expires_in_seconds) if expires_in_seconds is not None else None
        fingerprint = action_fingerprint(
            action=action,
            tool=tool,
            resource_scope=resource_scope,
            target=target,
            expected_effect=expected_effect,
            action_payload=action_payload,
        )
        return self._store.create_approval(
            run_id=run_id,
            agent_id=agent_id,
            issue_id=issue_id,
            project_id=project_id,
            action=action,
            tool=tool or None,
            resource_scope=resource_scope,
            target=target or None,
            expected_effect=expected_effect,
            action_payload=dict(action_payload or {}),
            action_fingerprint=fingerprint,
            request_metadata=dict(request_metadata or {}),
            status=APPROVAL_PENDING,
            requested_at=now,
            expires_at=expires_at,
        )

    # ------------------------------------------------------------------
    # Human decisions
    # ------------------------------------------------------------------
    def approve(self, approval_id: str, *, actor_id: str, feedback: str | None = None) -> dict[str, Any]:
        """Approve a pending, unexpired request; the decision is not reusable."""
        return self._decide(
            approval_id,
            actor_id=actor_id,
            feedback=feedback,
            from_statuses=(APPROVAL_PENDING,),
            status=APPROVAL_APPROVED,
            action="approve",
        )

    def reject(self, approval_id: str, *, actor_id: str, feedback: str | None = None) -> dict[str, Any]:
        """Reject a pending request; a rejected action can never execute."""
        return self._decide(
            approval_id,
            actor_id=actor_id,
            feedback=feedback,
            from_statuses=(APPROVAL_PENDING,),
            status=APPROVAL_REJECTED,
            action="reject",
        )

    def revoke(self, approval_id: str, *, actor_id: str, feedback: str | None = None) -> dict[str, Any]:
        """Revoke a pending or approved decision before it is executed."""
        now = self._now()
        self._store.expire_due(now)
        row = self._with_effective_status(self._require(approval_id), now)
        if row.get("executed_at") is not None:
            raise AgentApprovalError(
                "approval_already_executed",
                "an executed approval cannot be revoked",
            )
        status = str(row["status"])
        if status not in {APPROVAL_PENDING, APPROVAL_APPROVED}:
            raise AgentApprovalError(
                f"approval_{status}",
                f"approval is {status} and cannot be revoked",
            )
        updated = self._store.transition_approval(
            approval_id,
            from_statuses=(APPROVAL_PENDING, APPROVAL_APPROVED),
            status=APPROVAL_REVOKED,
            actor_id=actor_id,
            feedback=feedback,
            now=now,
        )
        if updated is None:
            self._raise_transition_conflict(approval_id, "revoke")
        return updated

    # ------------------------------------------------------------------
    # Execution gate
    # ------------------------------------------------------------------
    def execute(
        self,
        approval_id: str,
        *,
        run_id: str,
        agent_id: str,
        action: str,
        tool: str | None,
        resource_scope: str,
        target: str | None,
        expected_effect: str,
        action_payload: dict[str, Any] | None,
        authorization_allowed: bool,
    ) -> dict[str, Any]:
        """Consume an approved request after revalidating the exact action.

        Returns the consumed approval. Any failure raises
        :class:`AgentApprovalError` and leaves ``executed_at`` empty, so the
        caller cannot report success or perform the side effect.
        """
        now = self._now()
        self._store.expire_due(now)
        row = self._with_effective_status(self._require(approval_id), now)

        if str(row["agent_id"]) != agent_id or str(row["run_id"]) != run_id:
            raise AgentApprovalError(
                "approval_actor_mismatch",
                "approval does not belong to this agent run",
                status_code=403,
            )
        status = str(row["status"])
        if status != APPROVAL_APPROVED:
            raise AgentApprovalError(
                f"approval_{status}",
                f"approval is {status}; the action was not executed",
            )
        if row.get("executed_at") is not None:
            raise AgentApprovalError(
                "approval_already_used",
                "approval has already been consumed; request a new one",
            )
        if not authorization_allowed:
            raise AgentApprovalError(
                "approval_not_authorized",
                "the agent is no longer authorized for this action",
                status_code=403,
            )

        proposed = action_fingerprint(
            action=action,
            tool=tool,
            resource_scope=resource_scope,
            target=target,
            expected_effect=expected_effect,
            action_payload=action_payload,
        )
        if not hmac.compare_digest(proposed, str(row["action_fingerprint"])):
            raise AgentApprovalError(
                "approval_action_changed",
                "the action changed after approval; request a new approval",
            )

        consumed = self._store.consume_approval(
            approval_id,
            action_fingerprint=proposed,
            now=now,
        )
        if consumed is None:
            current = self._with_effective_status(self._require(approval_id), now)
            if current.get("executed_at") is not None:
                raise AgentApprovalError(
                    "approval_already_used",
                    "approval has already been consumed; request a new one",
                )
            if str(current["status"]) == APPROVAL_EXPIRED:
                raise AgentApprovalError(
                    "approval_expired",
                    "approval expired before execution",
                )
            raise AgentApprovalError(
                "approval_not_executable",
                "approval is no longer executable; request a new one",
            )
        return consumed

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _now(self) -> datetime:
        value = self._clock()
        return as_utc(value) or utcnow()

    def _require(self, approval_id: str) -> dict[str, Any]:
        row = self._store.get_approval(approval_id)
        if row is None:
            raise AgentApprovalError("approval_not_found", "approval not found", status_code=404)
        return row

    def _with_effective_status(self, row: dict[str, Any], now: datetime) -> dict[str, Any]:
        effective = effective_approval_status(
            str(row.get("status", "")),
            row.get("expires_at"),
            now=now,
        )
        if effective == row.get("status"):
            return row
        visible = dict(row)
        visible["status"] = effective
        return visible

    def _decide(
        self,
        approval_id: str,
        *,
        actor_id: str,
        feedback: str | None,
        from_statuses: Sequence[str],
        status: str,
        action: str,
    ) -> dict[str, Any]:
        now = self._now()
        self._store.expire_due(now)
        row = self._with_effective_status(self._require(approval_id), now)
        if row.get("executed_at") is not None:
            raise AgentApprovalError(
                "approval_already_executed",
                "an executed approval cannot be changed",
            )
        current = str(row["status"])
        if current not in from_statuses:
            raise AgentApprovalError(
                f"approval_{current}",
                f"approval is {current}; {action} is not allowed",
            )
        updated = self._store.transition_approval(
            approval_id,
            from_statuses=from_statuses,
            status=status,
            actor_id=actor_id,
            feedback=feedback,
            now=now,
        )
        if updated is None:
            self._raise_transition_conflict(approval_id, action)
        return updated

    def _raise_transition_conflict(self, approval_id: str, action: str) -> None:
        current = self._with_effective_status(self._require(approval_id), self._now())
        raise AgentApprovalError(
            f"approval_{current.get('status', 'unknown')}",
            f"approval could not transition to {action} because it is {current.get('status', 'unknown')}",
        )
