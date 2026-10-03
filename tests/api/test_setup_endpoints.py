"""Tests for the setup wizard endpoints (issue #543).

Runs without containers or network: the Neo4j setup store is replaced by an
in-memory fake and ``create_user`` (PostgreSQL bcrypt) is monkeypatched, the
same pattern used by ``test_chat_endpoints.py``.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import socialseed_tasker.infrastructure.web_api.routers.setup as setup_api
from socialseed_tasker.infrastructure.web_api.app import create_app


class FakeSetupStore:
    def __init__(self) -> None:
        self.installed_flag = False
        self.fail = False
        self.initialized: dict[str, Any] | None = None

    def installed(self) -> bool:
        if self.fail:
            raise setup_api.SetupStoreError("neo4j down")
        return self.installed_flag or self.initialized is not None

    def initialize(
        self,
        *,
        admin_username: str,
        project_name: str,
        project_summary: str,
        policies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if self.fail:
            raise setup_api.SetupStoreError("neo4j down")
        self.initialized = {
            "admin_username": admin_username,
            "project_name": project_name,
            "project_summary": project_summary,
            "policies": policies,
        }
        return {"projectId": "project-1"}


@pytest.fixture()
def setup_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TASKER_AUTH_ENABLED", "true")
    monkeypatch.setenv("TASKER_API_KEY", "test-token")
    for name in (
        "TASKER_INSTALLED",
        "TASKER_DATABASE_URL",
        "TASKER_MONGO_URL",
        "TASKER_REDIS_URL",
        "TASKER_INTEGRATION",
        "TASKER_AUTH_SEED",
        "TASKER_RATE_LIMIT_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    app = create_app()
    store = FakeSetupStore()
    app.state.setup_store = store
    user_calls: list[dict[str, Any]] = []

    def _fake_create_user(**kwargs: Any) -> str:
        user_calls.append(kwargs)
        return "created"

    monkeypatch.setattr(setup_api, "create_user", _fake_create_user)
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, store=store, user_calls=user_calls)


def _payload(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "admin_user": "admin",
        "admin_password": "admin",
        "project_name": "Mi Proyecto",
        "project_summary": "Resumen inicial",
        "policies": [],
        "custom_policies": [],
    }
    body.update(overrides)
    return body


def test_status_reports_pending_install_without_credentials(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"] == {"installed": False, "needSetup": True}


def test_status_env_override_forces_installed(setup_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_INSTALLED", "true")
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    assert resp.json()["data"] == {"installed": True, "needSetup": False}


def test_status_degrades_to_env_when_store_unavailable(
    setup_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_env.store.fail = True
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    assert resp.json()["data"]["installed"] is False

    monkeypatch.setenv("TASKER_INSTALLED", "true")
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    assert resp.json()["data"]["installed"] is True


def test_initialize_creates_admin_project_and_policies(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(
            admin_user="  Ad@min!  ",
            admin_password="",
            project_name="  Mi Proyecto  ",
            policies=["prevent_circular_dependencies", "require_solution_summary"],
            custom_policies=["Polimorfismo estricto en tipos de nodos"],
        ),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["installed"] is True
    assert data["adminUsername"] == "admin"
    assert data["projectName"] == "Mi Proyecto"
    assert data["projectId"] == "project-1"
    assert data["credentials"] == "created"
    assert len(data["policies"]) == 3

    assert setup_env.user_calls == [
        {"username": "admin", "password": "admin", "role": "ADMIN", "user_type": "admin"}
    ]

    initialized = setup_env.store.initialized
    assert initialized is not None
    assert initialized["admin_username"] == "admin"
    assert initialized["project_name"] == "Mi Proyecto"
    assert initialized["project_summary"] == "Resumen inicial"
    keys = [spec["key"] for spec in initialized["policies"]]
    assert keys == [
        "prevent_circular_dependencies",
        "require_solution_summary",
        "custom:Polimorfismo estricto en tipos de nodos",
    ]

    status = setup_env.client.get("/api/v1/setup/status")
    assert status.json()["data"] == {"installed": True, "needSetup": False}


def test_initialize_falls_back_to_default_credentials(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(admin_user="", admin_password="", project_name="Demo"),
    )
    assert resp.status_code == 200
    assert setup_env.user_calls[0]["username"] == "admin"
    assert setup_env.user_calls[0]["password"] == "admin"


def test_initialize_maps_all_predefined_policies(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(policies=list(setup_api.PREDEFINED_POLICIES)),
    )
    assert resp.status_code == 200
    specs = setup_env.store.initialized["policies"]
    assert [spec["key"] for spec in specs] == [
        "prevent_circular_dependencies",
        "require_solution_summary",
        "require_human_approval_core",
    ]
    assert {spec["severity"] for spec in specs} == {"BLOCKER", "WARNING"}
    assert all(spec["logic_definition"] for spec in specs)


def test_initialize_returns_403_when_already_installed(setup_env: SimpleNamespace) -> None:
    setup_env.store.installed_flag = True
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 403
    assert setup_env.store.initialized is None


def test_initialize_rejects_unknown_policy_key(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(policies=["not_a_policy"]),
    )
    assert resp.status_code == 400
    assert setup_env.store.initialized is None


def test_initialize_requires_project_name(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(project_name="   "),
    )
    assert resp.status_code == 400
    assert setup_env.store.initialized is None


def test_initialize_skips_postgres_when_not_configured(
    setup_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    from socialseed_tasker.auth import user_store

    monkeypatch.setattr(setup_api, "create_user", user_store.create_user)
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    assert resp.json()["data"]["credentials"] == "skipped"


def test_initialize_fails_with_503_when_store_unavailable(setup_env: SimpleNamespace) -> None:
    setup_env.store.fail = True
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 503
    assert setup_env.store.initialized is None
