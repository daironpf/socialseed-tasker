"""Unit tests for the retired legacy Keycloak SSO trio (issue #597).

``GET /auth/login`` was the only TIMEOUT of the 294-route smoke: it redirected
towards a Keycloak service the stack never ships. The trio now answers a
deterministic ``410 Gone`` (also with auth enabled, via a middleware
exemption) and is hidden from the OpenAPI schema, while ``POST
/api/v1/auth/login`` keeps working as the real login.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app

RETIRED_PATHS = ("/auth/login", "/auth/callback", "/auth/logout")


def _app(monkeypatch: pytest.MonkeyPatch, auth_enabled: bool = False) -> TestClient:
    for name in (
        "TASKER_AUTH_ENABLED",
        "TASKER_API_KEY",
        "TASKER_MONGO_URL",
        "TASKER_REDIS_URL",
        "TASKER_DATABASE_URL",
        "TASKER_INTEGRATION",
        "TASKER_RATE_LIMIT_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    if auth_enabled:
        monkeypatch.setenv("TASKER_AUTH_ENABLED", "true")
        monkeypatch.setenv("TASKER_API_KEY", "test-key-597")
    return TestClient(create_app())


def test_legacy_trio_answers_410_gone(monkeypatch: pytest.MonkeyPatch):
    with _app(monkeypatch) as client:
        for path in RETIRED_PATHS:
            method = client.post if path.endswith("logout") else client.get
            resp = method(path, follow_redirects=False)

            assert resp.status_code == 410, (path, resp.status_code)
            error = resp.json()["error"]
            assert error["code"] == "SSO_KEYCLOAK_RETIRED"
            assert "/api/v1/auth/login" in error["message"]


def test_legacy_trio_answers_410_even_with_auth_enabled(monkeypatch: pytest.MonkeyPatch):
    """Middleware exempts the trio so stale clients get the 410, not a 401."""
    with _app(monkeypatch, auth_enabled=True) as client:
        resp = client.get("/auth/login")
        assert resp.status_code == 410

        resp = client.get("/api/v1/users")
        assert resp.status_code == 401  # the real API stays guarded


def test_real_login_route_still_reachable_with_auth_enabled(monkeypatch: pytest.MonkeyPatch):
    with _app(monkeypatch, auth_enabled=True) as client:
        resp = client.post("/api/v1/auth/login", json={})

        assert resp.status_code != 410
        assert resp.status_code in (400, 401)  # missing credentials, not retired


def test_legacy_trio_hidden_from_openapi(monkeypatch: pytest.MonkeyPatch):
    with _app(monkeypatch) as client:
        paths = client.get("/openapi.json").json()["paths"]

        for path in RETIRED_PATHS:
            assert path not in paths
        assert "/api/v1/auth/login" in paths
