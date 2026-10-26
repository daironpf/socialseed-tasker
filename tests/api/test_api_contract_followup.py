"""Follow-up of the full-endpoint audit: DELETE routes and stricter specs.

Covers the three gaps reported after probing all 296 operations:

* ``DELETE /api/v1/data-quality/rules/{rule_id}`` — the registry already had a
  ``delete()`` method but no route, so live rules could never be removed.
* ``DELETE /api/v1/deployments/{id}`` — same story at the repository level.
* Request schemas that let invalid bodies through to hand-rolled 400s:
  secrets without ``name``/``value``, deployments without ``commit_sha``,
  direct conversations with fewer than two participants.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth.rbac import RBAC
from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.data_quality.rules import RuleRegistry
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.infrastructure.web_api.app import create_app

_UNIT_DIR = Path(__file__).resolve().parents[1] / "unit"

ADMIN_JWT = issue_tokens(
    {"id": "u-admin", "username": "u-admin", "role": "ADMIN", "permissions": ["admin"]}
)["access_token"]


@pytest.fixture()
def dq_env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    for name in ("TASKER_AUTH_USERS", "TASKER_AUTH_ENABLED", "TASKER_API_KEY",
                 "TASKER_REDIS_URL", "TASKER_DATABASE_URL", "TASKER_INTEGRATION"):
        monkeypatch.delenv(name, raising=False)
    registry = RuleRegistry(MemoryStorage())
    container = SimpleNamespace(rbac=RBAC(), rule_registry=registry, storage=MemoryStorage())
    monkeypatch.setattr(
        "socialseed_tasker.data_quality.api.build_default_container",
        lambda: container,
    )
    app = create_app()
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, registry=registry)


@pytest.fixture()
def client() -> TestClient:
    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    return TestClient(create_app(repository=MockRepository()))


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {ADMIN_JWT}"}


# -- data-quality: envelope + DELETE ----------------------------------------

def test_data_quality_reads_return_envelope(dq_env: SimpleNamespace) -> None:
    resp = dq_env.client.get("/api/v1/data-quality/rules")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["rules"] == []
    assert "meta" in body

    metrics = dq_env.client.get("/api/v1/data-quality/metrics")
    assert metrics.json()["data"]["metrics"] == {}

    report = dq_env.client.get("/api/v1/data-quality/reports/nope")
    assert report.json()["data"]["report"] == []


def test_delete_data_quality_rule_roundtrip_and_404(dq_env: SimpleNamespace) -> None:
    dq_env.registry.add(
        {"id": "rule-del", "name": "t", "kind": "not_empty", "target": "title"}
    )
    resp = dq_env.client.delete("/api/v1/data-quality/rules/rule-del", headers=_headers())
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["deleted"] is True
    assert dq_env.registry.get("rule-del") is None

    missing = dq_env.client.delete(
        "/api/v1/data-quality/rules/rule-del", headers=_headers()
    )
    assert missing.status_code == 404, missing.text


def test_delete_data_quality_rule_forbidden_without_admin(dq_env: SimpleNamespace) -> None:
    dq_env.registry.add(
        {"id": "rule-keep", "name": "t", "kind": "not_empty", "target": "title"}
    )
    resp = dq_env.client.delete("/api/v1/data-quality/rules/rule-keep")
    assert resp.status_code == 403, resp.text
    assert dq_env.registry.get("rule-keep") is not None


# -- deployments: DELETE -----------------------------------------------------

def test_delete_deployment_roundtrip_and_404(client: TestClient) -> None:
    created = client.post(
        "/api/v1/deployments",
        json={"commit_sha": "a" * 40, "environment": "PROD"},
    )
    assert created.status_code == 200, created.text
    deployment_id = created.json()["data"]["id"]

    resp = client.delete(f"/api/v1/deployments/{deployment_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["deleted"] is True

    listed = client.get("/api/v1/deployments")
    assert listed.json()["data"] == []

    missing = client.delete(f"/api/v1/deployments/{deployment_id}")
    assert missing.status_code == 404, missing.text


# -- stricter request specs (422 instead of hand-rolled 400) ----------------

def test_create_secret_requires_name_and_value(client: TestClient) -> None:
    no_name = client.post("/api/v1/secrets", json={"value": "aGk="})
    assert no_name.status_code == 422, no_name.text
    no_value = client.post("/api/v1/secrets", json={"name": "k"})
    assert no_value.status_code == 422, no_value.text


def test_create_deployment_requires_commit_sha(client: TestClient) -> None:
    resp = client.post("/api/v1/deployments", json={"environment": "PROD"})
    assert resp.status_code == 422, resp.text
    assert "commit_sha" in resp.text


def test_create_conversation_documents_and_enforces_participant_rule(
    client: TestClient,
) -> None:
    from socialseed_tasker.infrastructure.web_api.routers.chat import (
        ConversationCreateRequest,
    )

    field = ConversationCreateRequest.model_fields["participant_ids"]
    assert "exactly two participants" in (field.description or "")

    resp = client.post(
        "/api/v1/chat/conversations",
        json={"participant_ids": [], "type": "direct"},
        headers={"X-User-ID": "alice"},
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["message"] == "Invalid value for request"


def test_whoami_returns_envelope(client: TestClient) -> None:
    resp = client.get("/api/v1/whoami")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["authenticated"] is False
    assert "meta" in body
