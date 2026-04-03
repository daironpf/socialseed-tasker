"""Tests for the FastAPI REST API."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.entrypoints.web_api.app import create_app
from socialseed_tasker.storage.local_files.repositories import FileTaskRepository


@pytest.fixture()
def repo():
    tmp = Path(tempfile.mkdtemp())
    return FileTaskRepository(tmp)


@pytest.fixture()
def client(repo):
    app = create_app(repository=repo)
    return TestClient(app)


@pytest.fixture()
def component_id(client):
    resp = client.post(
        "/api/v1/components",
        json={"name": "Backend", "project": "test-project"},
    )
    return resp.json()["data"]["id"]


@pytest.fixture()
def issue_id(client, component_id):
    resp = client.post(
        "/api/v1/issues",
        json={
            "title": "Test issue",
            "component_id": component_id,
            "description": "A test issue",
            "priority": "HIGH",
            "labels": ["test"],
        },
    )
    return resp.json()["data"]["id"]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


class TestComponents:
    def test_create_component(self, client):
        resp = client.post(
            "/api/v1/components",
            json={"name": "API", "project": "my-project", "description": "REST API"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["data"]["name"] == "API"
        assert data["data"]["project"] == "my-project"
        assert data["error"] is None

    def test_list_components(self, client):
        client.post("/api/v1/components", json={"name": "A", "project": "p"})
        client.post("/api/v1/components", json={"name": "B", "project": "p"})
        resp = client.get("/api/v1/components")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_list_components_filter_by_project(self, client):
        client.post("/api/v1/components", json={"name": "A", "project": "proj1"})
        client.post("/api/v1/components", json={"name": "B", "project": "proj2"})
        resp = client.get("/api/v1/components", params={"project": "proj1"})
        assert len(resp.json()["data"]) == 1

    def test_get_component(self, client, component_id):
        resp = client.get(f"/api/v1/components/{component_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == component_id

    def test_get_missing_component_returns_404(self, client):
        resp = client.get("/api/v1/components/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------


class TestIssues:
    def test_create_issue(self, client, component_id):
        resp = client.post(
            "/api/v1/issues",
            json={
                "title": "Fix bug",
                "component_id": component_id,
                "priority": "CRITICAL",
                "labels": ["bug"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "Fix bug"
        assert data["priority"] == "CRITICAL"
        assert data["status"] == "OPEN"

    def test_create_issue_missing_component_returns_404(self, client):
        resp = client.post(
            "/api/v1/issues",
            json={"title": "Test", "component_id": "nonexistent"},
        )
        assert resp.status_code == 404

    def test_list_issues(self, client, component_id):
        client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        client.post(
            "/api/v1/issues",
            json={"title": "B", "component_id": component_id},
        )
        resp = client.get("/api/v1/issues")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 2

    def test_list_issues_pagination(self, client, component_id):
        for i in range(5):
            client.post(
                "/api/v1/issues",
                json={"title": f"Issue {i}", "component_id": component_id},
            )
        resp = client.get("/api/v1/issues", params={"page": 1, "limit": 2})
        data = resp.json()["data"]
        assert len(data["items"]) == 2
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["has_next"] is True

    def test_list_issues_filter_by_status(self, client, component_id):
        client.post(
            "/api/v1/issues",
            json={"title": "Open", "component_id": component_id},
        )
        resp = client.post(
            "/api/v1/issues",
            json={"title": "To close", "component_id": component_id},
        )
        issue_id = resp.json()["data"]["id"]
        client.post(f"/api/v1/issues/{issue_id}/close")

        resp = client.get("/api/v1/issues", params={"status": "OPEN"})
        assert len(resp.json()["data"]["items"]) == 1

    def test_get_issue(self, client, issue_id):
        resp = client.get(f"/api/v1/issues/{issue_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == issue_id

    def test_get_missing_issue_returns_404(self, client):
        resp = client.get("/api/v1/issues/nonexistent")
        assert resp.status_code == 404

    def test_update_issue(self, client, issue_id):
        resp = client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"title": "Updated title"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated title"

    def test_delete_issue(self, client, issue_id):
        resp = client.delete(f"/api/v1/issues/{issue_id}")
        assert resp.status_code == 204

        resp = client.get(f"/api/v1/issues/{issue_id}")
        assert resp.status_code == 404

    def test_close_issue(self, client, issue_id):
        resp = client.post(f"/api/v1/issues/{issue_id}/close")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "CLOSED"

    def test_close_issue_with_open_dependencies_returns_409(self, client, component_id):
        resp = client.post(
            "/api/v1/issues",
            json={"title": "Dependency", "component_id": component_id},
        )
        dep_id = resp.json()["data"]["id"]

        resp = client.post(
            "/api/v1/issues",
            json={"title": "Main", "component_id": component_id},
        )
        main_id = resp.json()["data"]["id"]

        client.post(
            f"/api/v1/issues/{main_id}/dependencies",
            json={"depends_on_id": dep_id},
        )

        resp = client.post(f"/api/v1/issues/{main_id}/close")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


class TestDependencies:
    def test_add_dependency(self, client, component_id):
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        resp_b = client.post(
            "/api/v1/issues",
            json={"title": "B", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        b_id = resp_b.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/issues/{a_id}/dependencies",
            json={"depends_on_id": b_id},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["issue_id"] == a_id
        assert resp.json()["data"]["depends_on_id"] == b_id

    def test_add_dependency_circular_returns_409(self, client, component_id):
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        resp_b = client.post(
            "/api/v1/issues",
            json={"title": "B", "component_id": component_id},
        )
        resp_c = client.post(
            "/api/v1/issues",
            json={"title": "C", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        b_id = resp_b.json()["data"]["id"]
        c_id = resp_c.json()["data"]["id"]

        client.post(f"/api/v1/issues/{a_id}/dependencies", json={"depends_on_id": b_id})
        client.post(f"/api/v1/issues/{b_id}/dependencies", json={"depends_on_id": c_id})
        # c -> a would create cycle
        resp = client.post(
            f"/api/v1/issues/{c_id}/dependencies",
            json={"depends_on_id": a_id},
        )
        assert resp.status_code == 409

    def test_remove_dependency(self, client, component_id):
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        resp_b = client.post(
            "/api/v1/issues",
            json={"title": "B", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        b_id = resp_b.json()["data"]["id"]

        client.post(f"/api/v1/issues/{a_id}/dependencies", json={"depends_on_id": b_id})
        resp = client.delete(f"/api/v1/issues/{a_id}/dependencies/{b_id}")
        assert resp.status_code == 204

    def test_list_dependencies(self, client, component_id):
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        resp_b = client.post(
            "/api/v1/issues",
            json={"title": "B", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        b_id = resp_b.json()["data"]["id"]

        client.post(f"/api/v1/issues/{a_id}/dependencies", json={"depends_on_id": b_id})
        resp = client.get(f"/api/v1/issues/{a_id}/dependencies")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_list_dependents(self, client, component_id):
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        resp_b = client.post(
            "/api/v1/issues",
            json={"title": "B", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        b_id = resp_b.json()["data"]["id"]

        client.post(f"/api/v1/issues/{a_id}/dependencies", json={"depends_on_id": b_id})
        resp = client.get(f"/api/v1/issues/{b_id}/dependents")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_dependency_chain(self, client, component_id):
        resp_c = client.post(
            "/api/v1/issues",
            json={"title": "C", "component_id": component_id},
        )
        resp_b = client.post(
            "/api/v1/issues",
            json={"title": "B", "component_id": component_id},
        )
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        b_id = resp_b.json()["data"]["id"]
        c_id = resp_c.json()["data"]["id"]

        client.post(f"/api/v1/issues/{a_id}/dependencies", json={"depends_on_id": b_id})
        client.post(f"/api/v1/issues/{b_id}/dependencies", json={"depends_on_id": c_id})

        resp = client.get(f"/api/v1/issues/{a_id}/dependency-chain")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_blocked_issues(self, client, component_id):
        resp_dep = client.post(
            "/api/v1/issues",
            json={"title": "Blocker", "component_id": component_id},
        )
        resp_blocked = client.post(
            "/api/v1/issues",
            json={"title": "Blocked", "component_id": component_id},
        )
        dep_id = resp_dep.json()["data"]["id"]
        blocked_id = resp_blocked.json()["data"]["id"]

        client.post(
            f"/api/v1/issues/{blocked_id}/dependencies",
            json={"depends_on_id": dep_id},
        )

        resp = client.get("/api/v1/blocked-issues")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1


# ---------------------------------------------------------------------------
# Error envelope consistency
# ---------------------------------------------------------------------------


class TestErrorEnvelope:
    def test_404_has_envelope(self, client):
        resp = client.get("/api/v1/issues/nonexistent")
        body = resp.json()
        assert "data" in body
        assert "error" in body
        assert "meta" in body
        assert body["error"]["code"] == "ISSUE_NOT_FOUND"

    def test_409_has_envelope(self, client, component_id):
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        # Close then try to close again
        client.post(f"/api/v1/issues/{a_id}/close")
        resp = client.post(f"/api/v1/issues/{a_id}/close")
        body = resp.json()
        assert resp.status_code == 409
        assert body["error"]["code"] == "ISSUE_ALREADY_CLOSED"


# ---------------------------------------------------------------------------
# Analysis endpoints
# ---------------------------------------------------------------------------


class TestAnalysis:
    def test_root_cause_with_matching_issue(self, client, component_id):
        # Create and close an issue with matching title
        resp_issue = client.post(
            "/api/v1/issues",
            json={
                "title": "Fix null pointer exception",
                "component_id": component_id,
                "description": "Fixed the NPE in user service",
            },
        )
        issue_id = resp_issue.json()["data"]["id"]
        client.post(f"/api/v1/issues/{issue_id}/close")

        # Submit a test failure that matches the issue
        resp = client.post(
            "/api/v1/analyze/root-cause",
            json={
                "test_id": "test_user_service",
                "test_name": "test_get_user",
                "error_message": "NullPointerException",
                "component": component_id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) > 0
        assert data["data"][0]["issue_id"] == issue_id
        assert data["data"][0]["confidence"] > 0

    def test_root_cause_invalid_body_returns_422(self, client):
        resp = client.post("/api/v1/analyze/root-cause", json={})
        assert resp.status_code == 422

    def test_root_cause_response_structure(self, client, component_id):
        # Create an issue
        resp_issue = client.post(
            "/api/v1/issues",
            json={
                "title": "Test issue",
                "component_id": component_id,
            },
        )
        issue_id = resp_issue.json()["data"]["id"]
        client.post(f"/api/v1/issues/{issue_id}/close")

        # Test returns proper envelope
        resp = client.post(
            "/api/v1/analyze/root-cause",
            json={
                "test_id": "test_xyz",
                "test_name": "test_xyz",
                "error_message": "xyz error",
                "component": "different-component",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "meta" in data

    def test_impact_analysis_with_dependents(self, client, component_id):
        # Create two issues with a dependency
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "Feature A", "component_id": component_id},
        )
        id_a = resp_a.json()["data"]["id"]

        resp_b = client.post(
            "/api/v1/issues",
            json={"title": "Feature B", "component_id": component_id},
        )
        id_b = resp_b.json()["data"]["id"]

        # Add dependency: A depends on B
        client.post(
            f"/api/v1/issues/{id_a}/dependencies",
            json={"depends_on_id": id_b},
        )

        resp = client.get(f"/api/v1/analyze/impact/{id_a}")
        assert resp.status_code == 200
        data = resp.json()
        assert "directly_affected" in data["data"]
        assert "risk_level" in data["data"]

    def test_impact_analysis_for_nonexistent_returns_empty(self, client):
        # The analyzer returns empty results for non-existent issues
        resp = client.get("/api/v1/analyze/impact/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["risk_level"] == "LOW"

    def test_impact_analysis_empty_for_isolated_issue(self, client, component_id):
        resp_issue = client.post(
            "/api/v1/issues",
            json={"title": "Isolated", "component_id": component_id},
        )
        issue_id = resp_issue.json()["data"]["id"]

        resp = client.get(f"/api/v1/analyze/impact/{issue_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["directly_affected"] == []
        assert data["data"]["transitively_affected"] == []
        assert data["data"]["risk_level"] == "LOW"
