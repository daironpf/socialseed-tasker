"""Unit tests for bidirectional GitHub sync (issue #522)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.domain.entities import CommentEntry, Component, Issue, IssuePriority
from socialseed_tasker.infrastructure.web_api.app import create_app
from test_api_routes_coverage import MockRepoFull

WEBHOOK_SECRET = "test-webhook-secret"
GITHUB_REPO_URL = "https://github.com/acme/app"


class SyncRepo(MockRepoFull):
    """MockRepoFull with working comment storage."""

    def add_comment(self, issue_id: str, text: str, author: str = "api-user") -> Issue:
        issue = self._issues[issue_id]
        comment = CommentEntry(author=author, text=text)
        updated = issue.model_copy(update={"comments": [*issue.comments, comment]})
        self._issues[issue_id] = updated
        return updated

    def get_comments(self, issue_id: str) -> list[dict[str, Any]]:
        return [
            {"id": str(c.id), "timestamp": c.timestamp, "author": c.author, "text": c.text}
            for c in self._issues[issue_id].comments
        ]


@pytest.fixture()
def repo():
    return SyncRepo()


@pytest.fixture()
def client(repo):
    app = create_app(repository=repo)
    return TestClient(app)


@pytest.fixture(autouse=True)
def webhook_secret_env():
    import socialseed_tasker.infrastructure.webhook_validator as validator_module

    previous = validator_module._validator_instance
    validator_module._validator_instance = None
    with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": WEBHOOK_SECRET}):
        yield
    validator_module._validator_instance = previous


def compute_signature(payload: str, secret: str) -> str:
    return f"sha256={hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()}"


def post_webhook(client: TestClient, event: str, payload: dict[str, Any]):
    body = json.dumps(payload)
    return client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": compute_signature(body, WEBHOOK_SECRET),
            "X-GitHub-Event": event,
            "Content-Type": "application/json",
        },
    )


def make_linked_issue(client: TestClient, repo: SyncRepo, github_number: int = 77, **issue_kwargs) -> str:
    component = Component(id=uuid4(), name=f"Comp-{uuid4().hex[:6]}", project="test", description="")
    repo.create_component(component)
    issue = Issue(
        title=issue_kwargs.pop("title", "Local title"),
        component_id=component.id,
        priority=IssuePriority.HIGH,
        **issue_kwargs,
    )
    repo.create_issue(issue)
    resp = client.post(
        f"/api/v1/issues/{issue.id}/link-github",
        params={"github_issue_url": f"{GITHUB_REPO_URL}/issues/{github_number}"},
    )
    assert resp.status_code == 200
    return str(issue.id)


def get_issue(client: TestClient, issue_id: str) -> dict[str, Any]:
    resp = client.get(f"/api/v1/issues/{issue_id}")
    assert resp.status_code == 200
    return resp.json()["data"]


class TestWebhookProcessing:
    def test_webhook_applies_remote_edit(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        resp = post_webhook(
            client,
            "issues",
            {
                "action": "edited",
                "issue": {
                    "number": 77,
                    "title": "Remote title",
                    "body": "remote body",
                    "state": "open",
                    "labels": [{"name": "bug"}],
                },
            },
        )
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["title"] == "Remote title"
        assert data["description"] == "remote body"
        assert data["labels"] == ["bug"]
        assert data["github_sync"]["sync_status"] == "SYNCED"
        assert data["github_sync"]["conflict"] is None

    def test_webhook_detects_double_edit_conflict(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        patch_resp = client.patch(f"/api/v1/issues/{issue_id}", json={"title": "Local edit"})
        assert patch_resp.status_code == 200

        resp = post_webhook(
            client,
            "issues",
            {
                "action": "edited",
                "issue": {"number": 77, "title": "Remote title", "body": "", "state": "open", "labels": []},
            },
        )
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["title"] == "Local edit"
        assert data["github_sync"]["sync_status"] == "CONFLICT"
        conflict = data["github_sync"]["conflict"]
        assert conflict["fields"] == ["title"]
        assert conflict["local"]["title"] == "Local edit"
        assert conflict["remote"]["title"] == "Remote title"

    def test_webhook_closed_applies_status(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        post_webhook(
            client,
            "issues",
            {"action": "closed", "issue": {"number": 77, "title": "Local title", "body": "", "state": "closed", "labels": []}},
        )
        data = get_issue(client, issue_id)
        assert data["status"] == "CLOSED"
        assert data["github_sync"]["sync_status"] == "SYNCED"

    def test_webhook_unlinked_issue_is_ignored(self, client, repo):
        component = Component(id=uuid4(), name="Solo", project="test", description="")
        repo.create_component(component)
        issue = Issue(title="Unlinked", component_id=component.id, priority=IssuePriority.LOW)
        repo.create_issue(issue)
        resp = post_webhook(
            client,
            "issues",
            {"action": "edited", "issue": {"number": 999, "title": "X", "body": "", "state": "open", "labels": []}},
        )
        assert resp.status_code == 200
        data = get_issue(client, str(issue.id))
        assert data["title"] == "Unlinked"
        assert data["github_sync"] is None

    def test_webhook_logs_include_detail(self, client, repo):
        make_linked_issue(client, repo)
        post_webhook(
            client,
            "issues",
            {"action": "edited", "issue": {"number": 77, "title": "Remote title", "body": "", "state": "open", "labels": []}},
        )
        resp = client.get("/api/v1/webhooks/github/logs")
        assert resp.status_code == 200
        details = [entry.get("detail") for entry in resp.json()["data"]]
        assert any(detail and "applied" in detail for detail in details)


class TestWebhookComments:
    def test_issue_comment_added_to_linked_issue(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        resp = post_webhook(
            client,
            "issue_comment",
            {
                "action": "created",
                "comment": {"body": "hello from GitHub", "user": {"login": "octo"}},
                "issue": {"number": 77},
            },
        )
        assert resp.status_code == 200
        comments = client.get(f"/api/v1/issues/{issue_id}/comments").json()["data"]
        assert len(comments) == 1
        assert comments[0]["text"] == "hello from GitHub"
        assert comments[0]["author"] == "octo"
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "SYNCED"

    def test_tasker_echo_comment_is_skipped(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        post_webhook(
            client,
            "issue_comment",
            {
                "action": "created",
                "comment": {
                    "body": "<!-- socialseed-tasker -->\npushed from Tasker",
                    "user": {"login": "octo"},
                },
                "issue": {"number": 77},
            },
        )
        comments = client.get(f"/api/v1/issues/{issue_id}/comments").json()["data"]
        assert comments == []


class TestWebhookPullRequest:
    def test_pull_request_event_stores_pr_url(self, client, repo):
        issue_id = make_linked_issue(client, repo, github_number=88)
        resp = post_webhook(
            client,
            "pull_request",
            {
                "action": "synchronize",
                "pull_request": {"number": 88, "html_url": f"{GITHUB_REPO_URL}/pull/88", "state": "open", "merged": False},
            },
        )
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["github_sync"]["pr_url"] == f"{GITHUB_REPO_URL}/pull/88"
        assert data["github_sync"]["sync_status"] == "SYNCED"

    def test_merged_pull_request_closes_issue(self, client, repo):
        issue_id = make_linked_issue(client, repo, github_number=89)
        post_webhook(
            client,
            "pull_request",
            {
                "action": "closed",
                "pull_request": {"number": 89, "html_url": f"{GITHUB_REPO_URL}/pull/89", "state": "closed", "merged": True},
            },
        )
        data = get_issue(client, issue_id)
        assert data["status"] == "CLOSED"
        assert data["github_sync"]["sync_status"] == "SYNCED"


class TestConflictResolution:
    def _conflicted(self, client, repo) -> str:
        issue_id = make_linked_issue(client, repo)
        client.patch(f"/api/v1/issues/{issue_id}", json={"title": "Local edit"})
        post_webhook(
            client,
            "issues",
            {"action": "edited", "issue": {"number": 77, "title": "Remote title", "body": "", "state": "open", "labels": []}},
        )
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "CONFLICT"
        return issue_id

    def test_resolve_keep_remote_applies_github_values(self, client, repo):
        issue_id = self._conflicted(client, repo)
        resp = client.post(
            f"/api/v1/issues/{issue_id}/github-sync/resolve",
            json={"resolution": "remote"},
        )
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["title"] == "Remote title"
        assert data["github_sync"]["sync_status"] == "SYNCED"
        assert data["github_sync"]["conflict"] is None

    def test_resolve_keep_local_pushes_to_github(self, client, repo):
        issue_id = self._conflicted(client, repo)
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            resp = client.post(
                f"/api/v1/issues/{issue_id}/github-sync/resolve",
                json={"resolution": "local"},
            )
        assert resp.status_code == 200
        adapter_cls.return_value.update_issue.assert_called_once_with(77, title="Local edit")
        data = get_issue(client, issue_id)
        assert data["title"] == "Local edit"
        assert data["github_sync"]["sync_status"] == "SYNCED"
        assert data["github_sync"]["conflict"] is None

    def test_resolve_merge_applies_and_pushes_merged_values(self, client, repo):
        issue_id = self._conflicted(client, repo)
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            resp = client.post(
                f"/api/v1/issues/{issue_id}/github-sync/resolve",
                json={"resolution": "merge", "fields": {"title": "Merged title"}},
            )
        assert resp.status_code == 200
        adapter_cls.return_value.update_issue.assert_called_once_with(77, title="Merged title")
        data = get_issue(client, issue_id)
        assert data["title"] == "Merged title"
        assert data["github_sync"]["sync_status"] == "SYNCED"
        assert data["github_sync"]["conflict"] is None

    def test_resolve_without_conflict_returns_400(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        resp = client.post(
            f"/api/v1/issues/{issue_id}/github-sync/resolve",
            json={"resolution": "local"},
        )
        assert resp.status_code == 400

    def test_resolve_push_failure_reports_error(self, client, repo):
        issue_id = self._conflicted(client, repo)
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            adapter_cls.return_value.update_issue.side_effect = RuntimeError("boom")
            resp = client.post(
                f"/api/v1/issues/{issue_id}/github-sync/resolve",
                json={"resolution": "local"},
            )
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "ERROR"
        assert "boom" in data["github_sync"]["error"]


class TestLocalPushToGitHub:
    def test_patch_pushes_mirrored_fields(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            resp = client.patch(f"/api/v1/issues/{issue_id}", json={"title": "New title"})
        assert resp.status_code == 200
        adapter_cls.return_value.update_issue.assert_called_once_with(77, title="New title")
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "SYNCED"
        assert data["github_sync"]["error"] is None

    def test_patch_push_failure_sets_visible_error(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        resp = client.patch(f"/api/v1/issues/{issue_id}", json={"title": "New title"})
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "ERROR"
        assert "not configured" in data["github_sync"]["error"]

    def test_patch_without_mirrored_fields_does_not_push(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            resp = client.patch(f"/api/v1/issues/{issue_id}", json={"priority": "LOW"})
        assert resp.status_code == 200
        adapter_cls.return_value.update_issue.assert_not_called()
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "SYNCED"


class TestForceResync:
    def test_resync_requires_link(self, client, repo):
        component = Component(id=uuid4(), name="Solo", project="test", description="")
        repo.create_component(component)
        issue = Issue(title="Unlinked", component_id=component.id, priority=IssuePriority.LOW)
        repo.create_issue(issue)
        resp = client.post(f"/api/v1/issues/{issue.id}/github-sync")
        assert resp.status_code == 400

    def test_resync_pulls_remote_state(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        remote = SimpleNamespace(title="Remote title", body="remote body", state="open", labels=["bug"])
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            adapter_cls.return_value.get_issue.return_value = remote
            resp = client.post(f"/api/v1/issues/{issue_id}/github-sync")
        assert resp.status_code == 200
        adapter_cls.return_value.get_issue.assert_called_once_with(77)
        data = get_issue(client, issue_id)
        assert data["title"] == "Remote title"
        assert data["github_sync"]["sync_status"] == "SYNCED"

    def test_resync_unconfigured_reports_error(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        resp = client.post(f"/api/v1/issues/{issue_id}/github-sync")
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "ERROR"
        assert "not configured" in data["github_sync"]["error"]

    def test_resync_detects_conflict_when_local_changed(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            adapter_cls.return_value.update_issue.side_effect = RuntimeError("offline")
            client.patch(f"/api/v1/issues/{issue_id}", json={"title": "Local edit"})
        remote = SimpleNamespace(title="Remote title", body="", state="open", labels=[])
        with patch("socialseed_tasker.application.github_sync.GitHubAdapter") as adapter_cls:
            adapter_cls.return_value.get_issue.return_value = remote
            resp = client.post(f"/api/v1/issues/{issue_id}/github-sync")
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["github_sync"]["sync_status"] == "CONFLICT"
        assert data["github_sync"]["conflict"]["fields"] == ["title"]


class TestGitHubSyncRepresentation:
    def test_link_exposes_github_sync_block(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        data = get_issue(client, issue_id)
        sync = data["github_sync"]
        assert sync is not None
        assert sync["issue_number"] == 77
        assert sync["github_url"] == f"{GITHUB_REPO_URL}/issues/77"
        assert sync["sync_status"] == "SYNCED"
        assert sync["last_synced_at"] is not None

    def test_link_accepts_pull_request_url(self, client, repo):
        component = Component(id=uuid4(), name="CompPR", project="test", description="")
        repo.create_component(component)
        issue = Issue(title="PR linked", component_id=component.id, priority=IssuePriority.MEDIUM)
        repo.create_issue(issue)
        resp = client.post(
            f"/api/v1/issues/{issue.id}/link-github",
            params={"github_issue_url": f"{GITHUB_REPO_URL}/pull/101"},
        )
        assert resp.status_code == 200
        data = get_issue(client, str(issue.id))
        assert data["github_sync"]["issue_number"] == 101

    def test_unlink_clears_github_sync_block(self, client, repo):
        issue_id = make_linked_issue(client, repo)
        resp = client.post(f"/api/v1/issues/{issue_id}/unlink-github")
        assert resp.status_code == 200
        data = get_issue(client, issue_id)
        assert data["github_sync"] is None
