"""Integration tests for multi-dependency health reporting (issue #533)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app

ALLOWED_STATES = ("connected", "disconnected", "not configured")


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestHealthDependencies:
    def test_reports_redis_and_postgres(self, client: TestClient) -> None:
        deps = client.get("/health").json()["dependencies"]
        assert deps["neo4j"] in ALLOWED_STATES
        assert deps["redis"] in ALLOWED_STATES
        assert deps["postgres"] in ALLOWED_STATES

    def test_not_configured_without_env(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
        monkeypatch.delenv("TASKER_DATABASE_URL", raising=False)
        data = client.get("/health").json()
        assert data["dependencies"]["redis"] == "not configured"
        assert data["dependencies"]["postgres"] == "not configured"
        assert data["status"] == "healthy"
        assert "redis" not in data["dependency_latency_ms"]
        assert "postgres" not in data["dependency_latency_ms"]

    def test_redis_unreachable_degrades(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TASKER_REDIS_URL", "redis://127.0.0.1:1/0")
        data = client.get("/health").json()
        assert data["dependencies"]["redis"] == "disconnected"
        assert data["status"] == "degraded"
        assert data["dependency_latency_ms"]["redis"] >= 0

    def test_postgres_unreachable_degrades(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TASKER_DATABASE_URL", "postgresql://tasker:tasker@127.0.0.1:1/tasker")
        data = client.get("/health").json()
        assert data["dependencies"]["postgres"] == "disconnected"
        assert data["status"] == "degraded"
        assert data["dependency_latency_ms"]["postgres"] >= 0

    def test_api_v1_alias_serves_same_payload(self, client: TestClient) -> None:
        root = client.get("/health")
        alias = client.get("/api/v1/health")
        assert root.status_code == 200
        assert alias.status_code == 200
        assert alias.json()["dependencies"] == root.json()["dependencies"]

    def test_api_v1_health_alias_skips_auth(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TASKER_API_KEY", "secret-key")
        monkeypatch.setenv("TASKER_AUTH_ENABLED", "true")
        app = create_app()
        client = TestClient(app)
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/issues").status_code == 401
