"""Admin guards accept login JWTs without TASKER_AUTH_USERS (issue #593).

``/admin/tenants`` and ``POST /data-quality/rules`` resolved identity only via
the static-token auth provider and permissions only via the RBAC store fed
from ``TASKER_AUTH_USERS`` — an env var the stack never defines — so even a
valid admin JWT from ``/auth/login`` got a systematic 403. Both surfaces now
share the unified ``require_permission`` policy (static token / JWT claims /
session cookie), while anonymous or under-privileged callers still get 403.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth.rbac import RBAC
from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.web_api.app import create_app

ADMIN_JWT = issue_tokens(
    {"id": "u-admin", "username": "u-admin", "role": "ADMIN", "permissions": ["admin"]}
)["access_token"]
DEV_JWT = issue_tokens(
    {"id": "u-dev", "username": "u-dev", "role": "DEVELOPER", "permissions": ["read:context"]}
)["access_token"]

RULE_BODY = {
    "id": "rule-593",
    "name": "name not empty",
    "kind": "not_empty",
    "target": "name",
}


class FakeTenantStore:
    def __init__(self) -> None:
        self.tenants: dict[str, dict] = {"existing": {"id": "existing", "config": {}}}
        self.deleted: list[str] = []

    def list_tenants(self) -> list[dict]:
        return list(self.tenants.values())

    def get_tenant(self, tenant_id: str) -> dict | None:
        return self.tenants.get(tenant_id)

    def delete_tenant(self, tenant_id: str) -> None:
        self.deleted.append(tenant_id)
        self.tenants.pop(tenant_id, None)


class FakeRuleRegistry:
    def __init__(self) -> None:
        self.added: list[dict] = []

    def add(self, spec: dict) -> None:
        self.added.append(spec)

    def list(self) -> list[dict]:
        return list(self.added)


def _headers(jwt: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt}"}


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in (
        "TASKER_AUTH_USERS",
        "TASKER_AUTH_ENABLED",
        "TASKER_API_KEY",
        "TASKER_REDIS_URL",
        "TASKER_DATABASE_URL",
        "TASKER_INTEGRATION",
    ):
        monkeypatch.delenv(name, raising=False)
    app = create_app()
    tenant_store = FakeTenantStore()
    app.state.container = SimpleNamespace(rbac=RBAC(), tenant_store=tenant_store)

    rule_registry = FakeRuleRegistry()
    dq_container = SimpleNamespace(rbac=RBAC(), rule_registry=rule_registry)
    monkeypatch.setattr(
        "socialseed_tasker.data_quality.api.build_default_container",
        lambda: dq_container,
    )
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            tenant_store=tenant_store,
            rule_registry=rule_registry,
        )


def test_admin_tenants_allows_admin_jwt_without_users_env(env: SimpleNamespace) -> None:
    resp = env.client.get("/api/v1/admin/tenants", headers=_headers(ADMIN_JWT))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["tenants"] == [{"id": "existing", "config": {}}]


def test_admin_tenants_get_and_delete_with_admin_jwt(env: SimpleNamespace) -> None:
    resp = env.client.get("/api/v1/admin/tenants/existing", headers=_headers(ADMIN_JWT))
    assert resp.status_code == 200, resp.text

    resp = env.client.delete("/api/v1/admin/tenants/existing", headers=_headers(ADMIN_JWT))
    assert resp.status_code == 200, resp.text
    assert env.tenant_store.deleted == ["existing"]


def test_admin_tenants_forbidden_for_developer_jwt(env: SimpleNamespace) -> None:
    resp = env.client.get("/api/v1/admin/tenants", headers=_headers(DEV_JWT))
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "forbidden"


def test_admin_tenants_forbidden_without_identity(env: SimpleNamespace) -> None:
    resp = env.client.get("/api/v1/admin/tenants")
    assert resp.status_code == 403, resp.text


def test_admin_tenants_static_token_uses_provider_permissions(env: SimpleNamespace) -> None:
    # auth/users.json grants "admin" to the static token even with the RBAC
    # store empty (TASKER_AUTH_USERS undefined).
    resp = env.client.get("/api/v1/admin/tenants", headers=_headers("admintoken123"))
    assert resp.status_code == 200, resp.text


def test_admin_tenants_static_reader_token_forbidden(env: SimpleNamespace) -> None:
    resp = env.client.get("/api/v1/admin/tenants", headers=_headers("readertoken123"))
    assert resp.status_code == 403, resp.text


def test_data_quality_rule_write_allows_admin_jwt(env: SimpleNamespace) -> None:
    resp = env.client.post(
        "/api/v1/data-quality/rules", json=RULE_BODY, headers=_headers(ADMIN_JWT)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["rule"]["id"] == "rule-593"
    assert env.rule_registry.added[0]["id"] == "rule-593"


def test_data_quality_rule_write_forbidden_for_developer_jwt(env: SimpleNamespace) -> None:
    resp = env.client.post(
        "/api/v1/data-quality/rules", json=RULE_BODY, headers=_headers(DEV_JWT)
    )
    assert resp.status_code == 403, resp.text
    assert env.rule_registry.added == []


def test_data_quality_rule_write_rejects_unknown_kind(env: SimpleNamespace) -> None:
    resp = env.client.post(
        "/api/v1/data-quality/rules",
        json={**RULE_BODY, "id": "rule-bogus", "kind": "bogus_kind"},
        headers=_headers(ADMIN_JWT),
    )
    assert resp.status_code == 422, resp.text
    assert "unsupported rule kind" in resp.text
    assert env.rule_registry.added == []


def test_data_quality_rule_write_forbidden_without_identity(env: SimpleNamespace) -> None:
    resp = env.client.post("/api/v1/data-quality/rules", json=RULE_BODY)
    assert resp.status_code == 403, resp.text


def test_data_quality_reads_stay_open_for_getters(env: SimpleNamespace) -> None:
    # GET /rules had no guard before and must keep working unauthenticated.
    resp = env.client.get("/api/v1/data-quality/rules")
    assert resp.status_code == 200, resp.text
