"""Bidirectional GitHub synchronization for linked issues (issue #522).

Implements a content-based three-way merge between the local issue, the last
state known from GitHub (``github_base``) and the incoming GitHub state, plus
the push path used when the issue is edited from the Tasker UI.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

from socialseed_tasker.application.actions import TaskRepositoryInterface
from socialseed_tasker.domain.entities import Issue, IssueStatus
from socialseed_tasker.infrastructure.github_adapter import GitHubAdapter

GITHUB_SYNC_FIELDS = ("title", "description", "status", "labels")
TASKER_COMMENT_MARKER = "<!-- socialseed-tasker -->"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _raw(value: Any) -> Any:
    return getattr(value, "value", value)


def _norm_status(value: Any) -> str:
    text = str(_raw(value) or "")
    return "CLOSED" if text == "CLOSED" else "OPEN"


def _base_value(field: str, value: Any) -> Any:
    if field == "status":
        return _norm_status(value)
    if field == "labels":
        return sorted(str(item) for item in (value or []))
    return str(value or "")


def issue_snapshot(issue: Issue) -> dict[str, Any]:
    """Normalized snapshot of the fields mirrored with GitHub."""
    return {
        "title": issue.title or "",
        "description": issue.description or "",
        "status": _norm_status(issue.status),
        "labels": sorted(str(label) for label in (issue.labels or [])),
    }


def remote_fields_from_payload(gh_issue: dict[str, Any]) -> dict[str, Any]:
    """Map a GitHub issue payload (or API body) onto local field names."""
    labels: list[str] = []
    for label in gh_issue.get("labels") or []:
        labels.append(str(label.get("name", "")) if isinstance(label, dict) else str(label))
    return {
        "title": str(gh_issue.get("title") or ""),
        "description": str(gh_issue.get("body") or ""),
        "status": "CLOSED" if gh_issue.get("state") == "closed" else "OPEN",
        "labels": labels,
    }


def _same(field: str, left: Any, right: Any) -> bool:
    if field == "status":
        return _norm_status(left) == _norm_status(right)
    if field == "labels":
        return sorted(str(item) for item in (left or [])) == sorted(str(item) for item in (right or []))
    return str(left or "") == str(right or "")


def compute_merge(
    issue: Issue, remote: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    """Three-way merge of local, base and remote mirrored fields.

    Returns ``(applies, conflict, new_base)`` where ``applies`` holds remote
    values safe to write locally, ``conflict`` describes fields edited on both
    sides, and ``new_base`` is the updated GitHub-known state.
    """
    local = issue_snapshot(issue)
    local_raw: dict[str, Any] = {
        "title": issue.title or "",
        "description": issue.description or "",
        "status": _raw(issue.status),
        "labels": list(issue.labels or []),
    }
    base = issue.github_base if isinstance(issue.github_base, dict) else None
    if not base:
        base = dict(local)
    applies: dict[str, Any] = {}
    conflict: dict[str, Any] | None = None
    new_base = dict(base)
    for field in GITHUB_SYNC_FIELDS:
        local_changed = not _same(field, local[field], base.get(field))
        remote_changed = not _same(field, remote[field], base.get(field))
        if remote_changed and not local_changed:
            applies[field] = remote[field]
            new_base[field] = _base_value(field, remote[field])
        elif remote_changed and local_changed:
            if _same(field, local_raw[field], remote[field]):
                new_base[field] = _base_value(field, remote[field])
            else:
                if conflict is None:
                    conflict = {"fields": [], "local": {}, "remote": {}, "detected_at": now_iso()}
                conflict["fields"].append(field)
                conflict["local"][field] = local_raw[field]
                conflict["remote"][field] = remote[field]
    return applies, conflict, new_base


def _field_updates(values: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if "title" in values:
        updates["title"] = str(values["title"] or "")[:200] or "Untitled Issue"
    if "description" in values:
        updates["description"] = str(values["description"] or "")
    if "status" in values:
        with suppress(ValueError):
            updates["status"] = IssueStatus(str(_raw(values["status"])))
    if "labels" in values:
        updates["labels"] = [str(item) for item in (values["labels"] or [])]
    return updates


def _sync_metadata(
    status: str = "SYNCED",
    error: str | None = None,
    conflict: Any = None,
    base: dict[str, Any] | None = None,
    synced: bool = True,
) -> dict[str, Any]:
    updates: dict[str, Any] = {
        "github_sync_status": status,
        "github_error": error,
        "github_conflict": conflict,
    }
    if synced:
        updates["github_last_synced_at"] = now_iso()
    if base is not None:
        updates["github_base"] = base
    return updates


def _get_adapter() -> GitHubAdapter:
    adapter = GitHubAdapter()
    if not adapter.is_configured:
        raise RuntimeError("GitHub sync is not configured (GITHUB_TOKEN / GITHUB_REPO)")
    return adapter


def _push_values(issue: Issue, values: dict[str, Any]) -> None:
    if issue.github_issue_number is None:
        return
    adapter = _get_adapter()
    kwargs: dict[str, Any] = {}
    if "title" in values:
        kwargs["title"] = str(values["title"] or "")[:200]
    if "description" in values:
        kwargs["body"] = str(values["description"] or "")
    if "status" in values:
        kwargs["state"] = "closed" if _norm_status(values["status"]) == "CLOSED" else "open"
    if "labels" in values:
        kwargs["labels"] = [str(item) for item in (values["labels"] or [])]
    if not kwargs:
        return
    adapter.update_issue(issue.github_issue_number, **kwargs)


def find_linked_issue(repo: TaskRepositoryInterface, github_number: Any) -> Issue | None:
    """Find the local issue linked to a GitHub issue/PR number."""
    try:
        number = int(github_number)
    except (TypeError, ValueError):
        return None
    for issue in repo.list_issues():
        if issue.github_issue_number is not None and int(issue.github_issue_number) == number:
            return issue
    return None


def push_issue_to_github(issue: Issue, changed_fields: set[str]) -> dict[str, Any]:
    """Push mirrored field changes to GitHub; returns sync metadata updates."""
    fields = [field for field in changed_fields if field in GITHUB_SYNC_FIELDS]
    if not fields or not issue.github_issue_number:
        return {}
    snapshot = issue_snapshot(issue)
    values = {field: snapshot[field] for field in fields}
    try:
        _push_values(issue, values)
    except Exception as exc:
        return _sync_metadata(status="ERROR", error=str(exc)[:500], synced=False)
    base = issue.github_base if isinstance(issue.github_base, dict) else dict(snapshot)
    for field in fields:
        base[field] = snapshot[field]
    return _sync_metadata(base=base)


def pull_github_issue(repo: TaskRepositoryInterface, issue: Issue) -> Issue:
    """Pull the linked GitHub issue and merge it into the local issue."""
    if not issue.github_issue_number:
        raise ValueError("Issue not linked to GitHub")
    try:
        adapter = _get_adapter()
        gh_issue = adapter.get_issue(issue.github_issue_number)
    except Exception as exc:
        return repo.update_issue(str(issue.id), _sync_metadata(status="ERROR", error=str(exc)[:500], synced=False))
    remote = remote_fields_from_payload(
        {
            "title": gh_issue.title,
            "body": gh_issue.body,
            "state": gh_issue.state,
            "labels": [{"name": name} for name in gh_issue.labels],
        }
    )
    applies, conflict, new_base = compute_merge(issue, remote)
    if conflict is not None:
        return repo.update_issue(str(issue.id), _sync_metadata(status="CONFLICT", conflict=conflict, synced=False))
    updates = _field_updates(applies)
    updates.update(_sync_metadata(base=new_base))
    return repo.update_issue(str(issue.id), updates)


def resolve_github_conflict(
    repo: TaskRepositoryInterface,
    issue: Issue,
    resolution: str,
    merged_fields: dict[str, Any] | None = None,
) -> Issue:
    """Resolve a detected conflict: keep local, keep remote or merge values."""
    conflict = issue.github_conflict
    if not isinstance(conflict, dict) or not conflict.get("fields"):
        raise ValueError("Issue has no GitHub sync conflict")
    fields = [field for field in conflict.get("fields", []) if field in GITHUB_SYNC_FIELDS]
    local_vals = dict(conflict.get("local") or {})
    remote_vals = dict(conflict.get("remote") or {})

    if resolution == "local":
        values = {field: local_vals[field] for field in fields if field in local_vals}
        base_after = issue.github_base if isinstance(issue.github_base, dict) else issue_snapshot(issue)
        base_after = dict(base_after)
        try:
            _push_values(issue, values)
        except Exception as exc:
            return repo.update_issue(
                str(issue.id),
                _sync_metadata(status="ERROR", error=str(exc)[:500], conflict=None, synced=False),
            )
        for field in values:
            base_after[field] = _base_value(field, values[field])
        return repo.update_issue(str(issue.id), _sync_metadata(conflict=None, base=base_after))

    if resolution == "remote":
        values = {field: remote_vals[field] for field in fields if field in remote_vals}
        updates = _field_updates(values)
        base_after = issue.github_base if isinstance(issue.github_base, dict) else issue_snapshot(issue)
        base_after = dict(base_after)
        for field in values:
            base_after[field] = _base_value(field, values[field])
        updates.update(_sync_metadata(conflict=None, base=base_after))
        return repo.update_issue(str(issue.id), updates)

    if resolution == "merge":
        if not merged_fields:
            raise ValueError("Merge resolution requires field values")
        values = {field: merged_fields[field] for field in fields if field in merged_fields}
        if not values:
            raise ValueError("Merge resolution requires values for the conflicted fields")
        updates = _field_updates(values)
        base_after = issue.github_base if isinstance(issue.github_base, dict) else issue_snapshot(issue)
        base_after = dict(base_after)
        try:
            _push_values(issue, values)
        except Exception as exc:
            updates.update(_sync_metadata(status="ERROR", error=str(exc)[:500], conflict=None, synced=False))
            return repo.update_issue(str(issue.id), updates)
        for field in values:
            base_after[field] = _base_value(field, values[field])
        updates.update(_sync_metadata(conflict=None, base=base_after))
        return repo.update_issue(str(issue.id), updates)

    raise ValueError(f"Unknown resolution: {resolution}")


def _persist(repo: TaskRepositoryInterface, issue_id: str, updates: dict[str, Any]) -> None:
    if updates:
        repo.update_issue(issue_id, updates)


def apply_github_event(
    repo: TaskRepositoryInterface, event_type: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Apply a signed GitHub webhook event to the linked local issue."""
    action = str(payload.get("action") or "")
    summary: dict[str, Any] = {
        "event": event_type,
        "action": action,
        "status": "ignored",
        "issue_id": None,
        "changes": [],
        "conflict": False,
    }

    if event_type == "issues":
        gh_issue = payload.get("issue") or {}
        issue = find_linked_issue(repo, gh_issue.get("number"))
        if issue is None:
            summary["status"] = "not_linked"
            return summary
        if action in ("deleted", "transferred"):
            summary["issue_id"] = str(issue.id)
            summary["status"] = "ignored"
            return summary
        summary["issue_id"] = str(issue.id)
        remote = remote_fields_from_payload(gh_issue)
        applies, conflict, new_base = compute_merge(issue, remote)
        if conflict is not None:
            _persist(repo, str(issue.id), _sync_metadata(status="CONFLICT", conflict=conflict, synced=False))
            summary["status"] = "conflict"
            summary["conflict"] = True
            summary["changes"] = list(conflict.get("fields", []))
            return summary
        updates = _field_updates(applies)
        summary["changes"] = sorted(updates.keys())
        summary["status"] = "applied" if updates else "synced"
        updates.update(_sync_metadata(base=new_base))
        _persist(repo, str(issue.id), updates)
        return summary

    if event_type == "issue_comment":
        if action != "created":
            summary["status"] = "ignored"
            return summary
        comment = payload.get("comment") or {}
        body = str(comment.get("body") or "")
        gh_issue = payload.get("issue") or {}
        issue = find_linked_issue(repo, gh_issue.get("number"))
        if issue is None:
            summary["status"] = "not_linked"
            return summary
        summary["issue_id"] = str(issue.id)
        if TASKER_COMMENT_MARKER in body:
            summary["status"] = "ignored_echo"
            return summary
        user = comment.get("user") or {}
        author = str(user.get("login") or "github")
        repo.add_comment(issue_id=str(issue.id), text=body, author=author)
        _persist(repo, str(issue.id), _sync_metadata())
        summary["status"] = "applied"
        summary["changes"] = ["comments"]
        return summary

    if event_type == "pull_request":
        pull = payload.get("pull_request") or {}
        number = pull.get("number") if pull else payload.get("number")
        issue = find_linked_issue(repo, number)
        if issue is None:
            summary["status"] = "not_linked"
            return summary
        summary["issue_id"] = str(issue.id)
        pr_updates: dict[str, Any] = {
            "github_pr_url": pull.get("html_url"),
            "github_pr_number": pull.get("number"),
        }
        base: dict[str, Any] | None = None
        if action == "closed" and pull.get("merged") and _norm_status(issue.status) != "CLOSED":
            pr_updates["status"] = IssueStatus.CLOSED
            base = issue.github_base if isinstance(issue.github_base, dict) else issue_snapshot(issue)
            base = dict(base)
            base["status"] = "CLOSED"
            summary["changes"] = ["status"]
        pr_updates.update(_sync_metadata(base=base))
        summary["status"] = "applied"
        _persist(repo, str(issue.id), pr_updates)
        return summary

    return summary
