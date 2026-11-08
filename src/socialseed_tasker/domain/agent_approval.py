"""Approval decisions bound to one concrete agent action (issue #616).

The approval is identified by a fingerprint computed from every field that
changes the effect of the action. Presentation-only fields (title, diffs,
impact summary) never participate in the fingerprint, so re-rendering a request
cannot make an approval valid for a different operation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_REVOKED = "revoked"
APPROVAL_EXPIRED = "expired"

AGENT_APPROVAL_STATUSES = frozenset(
    {
        APPROVAL_PENDING,
        APPROVAL_APPROVED,
        APPROVAL_REJECTED,
        APPROVAL_REVOKED,
        APPROVAL_EXPIRED,
    }
)

# Only an approved decision that has not expired and has not been consumed can
# authorize execution. Pending and every negative state fail closed.
APPROVAL_EXECUTABLE_STATUSES = frozenset({APPROVAL_APPROVED})

AGENT_APPROVAL_ACTIONS = frozenset({"read", "propose", "apply"})


def utcnow() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    """Normalize a database/API timestamp to aware UTC when it is naive."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def effective_approval_status(
    status: str,
    expires_at: datetime | None,
    *,
    now: datetime | None = None,
) -> str:
    """Return the status visible to callers after applying the deadline.

    There is no deadline-free auto-approval: ``None`` keeps ``pending`` pending
    forever until a person decides or the request is revoked.
    """
    expiry = as_utc(expires_at)
    if status in {APPROVAL_PENDING, APPROVAL_APPROVED} and expiry is not None and expiry <= (now or utcnow()):
        return APPROVAL_EXPIRED
    return status


def canonical_action(
    *,
    action: str,
    tool: str | None,
    resource_scope: str,
    target: str | None,
    expected_effect: str,
    action_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build the normalized action snapshot that an approval covers."""
    return {
        "action": action,
        "tool": tool or None,
        "resource_scope": resource_scope,
        "target": target or None,
        "expected_effect": expected_effect,
        "action_payload": dict(action_payload or {}),
    }


def action_fingerprint(
    *,
    action: str,
    tool: str | None,
    resource_scope: str,
    target: str | None,
    expected_effect: str,
    action_payload: Mapping[str, Any] | None,
) -> str:
    """Hash the complete action/effect contract approved by a person.

    The hash is intentionally deterministic across Python processes: sorted
    keys, compact separators and no implicit coercion of the action fields.
    """
    snapshot = canonical_action(
        action=action,
        tool=tool,
        resource_scope=resource_scope,
        target=target,
        expected_effect=expected_effect,
        action_payload=action_payload,
    )
    encoded = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
