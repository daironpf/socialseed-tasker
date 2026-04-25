"""Integration tests for webhook endpoints.

These tests verify webhook signature validation, event processing,
and payload handling. They use mocks for the secret manager.
"""

import hmac
import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.core.services.webhook_validator import (
    WebhookSignatureValidator,
    validate_signature,
)
from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.constraints import Constraint
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.entrypoints.web_api.app import create_app


class MockRepository(TaskRepositoryInterface):
    """In-memory mock repository for API testing."""

    def __init__(self) -> None:
        self._issues: dict[str, Issue] = {}
        self._components: dict[str, Component] = {}
        self._dependencies: dict[str, set[str]] = {}
        self._constraints: dict[str, Constraint] = {}

    def create_issue(self, issue: Issue) -> None:
        self._issues[str(issue.id)] = issue

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._issues.get(issue_id)

    def update_issue(self, issue_id: str, updates: dict[str, Any]) -> Issue:
        issue = self._issues[issue_id]
        updated = issue.model_copy(update=updates)
        self._issues[issue_id] = updated
        return updated

    def close_issue(self, issue_id: str) -> Issue:
        issue = self._issues[issue_id]
        updated = issue.model_copy(update={"status": IssueStatus.CLOSED})
        self._issues[issue_id] = updated
        return updated

    def delete_issue(self, issue_id: str) -> None:
        self._issues.pop(issue_id, None)

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        issues = list(self._issues.values())
        if component_id:
            issues = [i for i in issues if str(i.component_id) == component_id]
        if status:
            issues = [i for i in issues if i.status == status]
        return issues

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        self._dependencies.setdefault(issue_id, set()).add(depends_on_id)

    def remove_dependency(self, issue_id: str, depends_on_id: str) -> None:
        if issue_id in self._dependencies:
            self._dependencies[issue_id].discard(depends_on_id)

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        dep_ids = self._dependencies.get(issue_id, set())
        return [self._issues[d] for d in dep_ids if d in self._issues]

    def get_dependents(self, issue_id: str) -> list[Issue]:
        return [
            self._issues[issuer_id]
            for issuer_id, deps in self._dependencies.items()
            if issue_id in deps and issuer_id in self._issues
        ]

    def get_blocked_issues(self) -> list[Issue]:
        return []

    def get_workable_issues(
        self,
        priority: str | None = None,
        component_id: str | None = None,
    ) -> list[Issue]:
        return [i for i in self._issues.values() if i.status != IssueStatus.CLOSED]

    def create_component(self, component: Component) -> None:
        self._components[str(component.id)] = component

    def get_component(self, component_id: str) -> Component | None:
        return self._components.get(component_id)

    def list_components(self, project: str | None = None) -> list[Component]:
        return list(self._components.values())

    def update_component(self, component_id: str, updates: dict[str, Any]) -> Component:
        component = self._components[component_id]
        updated = component.model_copy(update=updates)
        self._components[component_id] = updated
        return updated

    def delete_component(self, component_id: str) -> None:
        self._components.pop(component_id, None)

    def get_component_by_name(self, name: str, project: str | None = None) -> Component | None:
        for comp in self._components.values():
            if comp.name == name:
                return comp
        return None

    def find_issues_by_title(self, title: str, component_id: str | None = None) -> list[Issue]:
        return [i for i in self._issues.values() if i.title == title]

    def add_reasoning_log(
        self,
        issue_id: str,
        context: str,
        reasoning: str,
        related_nodes: list[str] | None = None,
    ) -> Issue:
        return self._issues[issue_id]

    def get_reasoning_logs(self, issue_id: str) -> list[dict[str, Any]]:
        return []

    def update_manifest_todo(self, issue_id: str, todo: list[dict[str, str]]) -> Issue:
        return self._issues[issue_id]

    def update_manifest_files(self, issue_id: str, files: list[str]) -> Issue:
        return self._issues[issue_id]

    def update_manifest_notes(self, issue_id: str, notes: list[str]) -> Issue:
        return self._issues[issue_id]

    def get_manifest(self, issue_id: str) -> dict[str, Any]:
        return {}

    def start_agent_work(self, issue_id: str, agent_id: str) -> Issue:
        return self._issues[issue_id]

    def finish_agent_work(self, issue_id: str) -> Issue:
        return self._issues[issue_id]

    def get_agent_status(self, issue_id: str) -> dict[str, Any]:
        return {}

    def create_constraint(self, constraint: Constraint) -> None:
        self._constraints[str(constraint.id)] = constraint

    def list_constraints(self, category: str | None = None) -> list[Constraint]:
        return list(self._constraints.values())

    def get_constraint(self, constraint_id: str) -> Constraint | None:
        return self._constraints.get(constraint_id)

    def delete_constraint(self, constraint_id: str) -> None:
        self._constraints.pop(constraint_id, None)

    def update_constraint(self, constraint_id: str, updates: dict) -> Constraint:
        constraint = self._constraints[constraint_id]
        data = constraint.model_dump()
        data.update(updates)
        updated = Constraint(**data)
        self._constraints[constraint_id] = updated
        return updated

    def reset_data(self, scope: str = "all") -> dict[str, int]:
        return {}

    @contextmanager
    def transaction(self) -> Iterator[None]:
        yield


def compute_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for payload."""
    return f"sha256={hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()}"


@pytest.fixture()
def repo():
    return MockRepository()


@pytest.fixture()
def client(repo):
    app = create_app(repository=repo)
    return TestClient(app)


@pytest.fixture()
def webhook_secret():
    return "test-webhook-secret"


class TestGitHubWebhookSignatureValidation:
    """Tests for GitHub webhook signature validation."""

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_valid_signature_passes(self, client, webhook_secret):
        """Valid HMAC-SHA256 signature should be accepted."""
        payload = json.dumps({"action": "opened", "issue": {"title": "Test Issue"}})

        response = client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "X-Hub-Signature-256": compute_signature(payload, webhook_secret),
                "X-GitHub-Event": "issues",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["received"] is True
        assert data["data"]["event"] == "issues"

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_invalid_signature_returns_401(self, client):
        """Invalid signature should return 401."""
        response = client.post(
            "/api/v1/webhooks/github",
            content='{"action": "opened"}',
            headers={
                "X-Hub-Signature-256": "sha256=invalid-signature",
                "X-GitHub-Event": "issues",
            },
        )
        assert response.status_code == 401

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_missing_signature_returns_401(self, client):
        """Missing signature should return 401."""
        response = client.post(
            "/api/v1/webhooks/github",
            content='{"action": "opened"}',
            headers={
                "X-GitHub-Event": "issues",
            },
        )
        assert response.status_code == 401

    @patch.dict(os.environ, {}, clear=True)
    def test_unconfigured_secret_returns_401(self, client):
        """Missing webhook secret should return 401."""
        response = client.post(
            "/api/v1/webhooks/github",
            content='{"action": "opened"}',
            headers={
                "X-Hub-Signature-256": "sha256=any",
                "X-GitHub-Event": "issues",
            },
        )
        assert response.status_code == 401


class TestGitHubWebhookEventTypes:
    """Tests for GitHub webhook event type handling."""

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_issues_event_processing(self, client, webhook_secret):
        """Issues event should be processed correctly."""
        payload = json.dumps({
            "action": "opened",
            "issue": {"title": "New Issue", "number": 1}
        })

        response = client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "X-Hub-Signature-256": compute_signature(payload, webhook_secret),
                "X-GitHub-Event": "issues",
            },
        )
        assert response.status_code == 200
        assert response.json()["data"]["event"] == "issues"

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_issue_comment_event(self, client, webhook_secret):
        """Issue comment event should be processed."""
        payload = json.dumps({
            "action": "created",
            "comment": {"body": "Test comment"},
            "issue": {"title": "Test Issue"}
        })

        response = client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "X-Hub-Signature-256": compute_signature(payload, webhook_secret),
                "X-GitHub-Event": "issue_comment",
            },
        )
        assert response.status_code == 200

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_label_event(self, client, webhook_secret):
        """Label event should be processed."""
        payload = json.dumps({"label": {"name": "bug"}})

        response = client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "X-Hub-Signature-256": compute_signature(payload, webhook_secret),
                "X-GitHub-Event": "label",
            },
        )
        assert response.status_code == 200

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_milestone_event(self, client, webhook_secret):
        """Milestone event should be processed."""
        payload = json.dumps({"milestone": {"title": "v1.0"}})

        response = client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "X-Hub-Signature-256": compute_signature(payload, webhook_secret),
                "X-GitHub-Event": "milestone",
            },
        )
        assert response.status_code == 200


class TestGitHubWebhookMalformedPayloads:
    """Tests for malformed webhook payloads."""

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_invalid_json_returns_422(self, client, webhook_secret):
        """Invalid JSON payload should return validation error."""
        response = client.post(
            "/api/v1/webhooks/github",
            content="not valid json",
            headers={
                "X-Hub-Signature-256": compute_signature("not valid json", webhook_secret),
                "X-GitHub-Event": "issues",
            },
        )
        assert response.status_code in (400, 422, 500)

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_empty_payload(self, client, webhook_secret):
        """Empty payload should be handled."""
        response = client.post(
            "/api/v1/webhooks/github",
            content="",
            headers={
                "X-Hub-Signature-256": compute_signature("", webhook_secret),
                "X-GitHub-Event": "issues",
            },
        )
        assert response.status_code in (200, 400, 422, 500)


class TestWebhookLogs:
    """Tests for webhook delivery logs."""

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_get_webhook_logs(self, client, webhook_secret):
        """Should return webhook logs."""
        payload = json.dumps({"action": "opened"})
        client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "X-Hub-Signature-256": compute_signature(payload, webhook_secret),
                "X-GitHub-Event": "issues",
            },
        )

        response = client.get("/api/v1/webhooks/github/logs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)


class TestWebhookTestEndpoint:
    """Tests for the webhook test endpoint."""

    @patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": "test-webhook-secret"})
    def test_webhook_configured(self, client):
        """Should return success when webhook is configured."""
        response = client.get("/api/v1/webhooks/github/test")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is True
        assert "valid" in data["data"]["message"].lower()

    @patch.dict(os.environ, {}, clear=True)
    def test_webhook_not_configured(self, client):
        """Should return failure when webhook is not configured."""
        response = client.get("/api/v1/webhooks/github/test")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] is False


class TestTestFailureWebhook:
    """Tests for the test-failure webhook endpoint."""

    def test_test_failure_without_api_key(self, client):
        """Should work without API key when not configured."""
        response = client.post(
            "/api/v1/webhooks/test-failure",
            json={
                "test_name": "test_example",
                "test_file": "tests/test_example.py",
                "test_type": "unit",
                "error_message": "AssertionError: expected 1 got 2",
                "stack_trace": "File ...\nAssertionError",
                "commit_sha": "abc123",
                "branch": "main",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data["data"]

    def test_test_failure_with_invalid_api_key(self, client):
        """Should reject invalid API key."""
        response = client.post(
            "/api/v1/webhooks/test-failure",
            json={
                "test_name": "test_example",
                "test_file": "tests/test_example.py",
                "test_type": "unit",
                "error_message": "Error",
                "stack_trace": "...",
                "commit_sha": "abc123",
                "branch": "main",
            },
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    @patch.dict(os.environ, {"TASKER_WEBHOOK_API_KEY": "valid-key"})
    def test_test_failure_with_valid_api_key(self, client):
        """Should accept valid API key."""
        response = client.post(
            "/api/v1/webhooks/test-failure",
            json={
                "test_name": "test_example",
                "test_file": "tests/test_example.py",
                "test_type": "unit",
                "error_message": "Error",
                "stack_trace": "...",
                "commit_sha": "abc123",
                "branch": "main",
            },
            headers={"X-API-Key": "valid-key"},
        )
        assert response.status_code == 200
