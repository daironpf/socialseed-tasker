"""Integration tests for the /health endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")

    def test_health_has_version_field(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_has_python_version(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "python_version" in data
        parts = data["python_version"].split(".")
        assert len(parts) >= 2
        assert all(p.isdigit() for p in parts)

    def test_health_has_dependencies(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "dependencies" in data
        assert isinstance(data["dependencies"], dict)
        assert "httpx" in data["dependencies"]
        assert data["dependencies"]["httpx"] in ("available", "not installed")

    def test_health_has_authentication_block(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "authentication" in data
        assert "enabled" in data["authentication"]
        assert "configured" in data["authentication"]

    def test_health_has_rate_limiting_block(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert "rate_limiting" in data
        assert "enabled" in data["rate_limiting"]

    def test_health_neo4j_status_not_configured(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["dependencies"]["neo4j"] == "not configured"
