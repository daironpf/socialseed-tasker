"""Tests for the mock-api FastAPI server (demo/e2e backend)."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_SERVER_PATH = Path(__file__).resolve().parents[2] / "mock-api" / "server.py"
_spec = importlib.util.spec_from_file_location("mock_api_server", _SERVER_PATH)
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture()
def client(data_dir):
    return TestClient(server.app)


def seed(name: str, payload: dict):
    (server.DATA_DIR / name).write_text(json.dumps(payload), encoding="utf-8")


def user(uid="u1", **over):
    base = {
        "id": uid,
        "username": f"user-{uid}",
        "email": f"{uid}@example.com",
        "role": "developer",
        "type": "human",
        "avatar": "U",
        "skills": [],
        "specialization": None,
        "issues_assigned": 0,
        "issues_created": 0,
        "last_active": "2026-01-01T00:00:00Z",
        "created_at": "2026-01-01T00:00:00Z",
        "is_active": True,
    }
    base.update(over)
    return base


def issue(iid="ISS-001", **over):
    base = {
        "id": iid,
        "title": f"Title {iid}",
        "description": "",
        "status": "OPEN",
        "priority": "MEDIUM",
        "component_id": "comp-1",
        "project_id": "socialseed-tasker",
        "assignee": None,
        "created_by": None,
        "labels": [],
        "dependencies": [],
        "blocks": [],
        "affects": [],
        "architectural_constraints": [],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "closed_at": None,
        "agent_working": False,
    }
    base.update(over)
    return base


# ---------------------------------------------------------------- helpers --


def test_read_json_missing_file_returns_empty(data_dir):
    assert server.read_json("missing.json") == {}


def test_write_json_roundtrip(data_dir):
    server.write_json("roundtrip.json", {"a": 1})
    assert server.read_json("roundtrip.json") == {"a": 1}


# ----------------------------------------------------------------- users --


def test_users_crud(client, data_dir):
    seed("users.json", {"users": [user()]})

    assert client.get("/mock/users").json()["data"] == [user()]
    assert client.get("/mock/users/u1").json()["data"]["id"] == "u1"
    assert client.get("/mock/users/nope").status_code == 404

    updated = client.put("/mock/users/u1", json={"role": "lead"}).json()["data"]
    assert updated["role"] == "lead"
    assert updated["username"] == "user-u1"  # untouched fields preserved
    assert client.put("/mock/users/nope", json={"role": "lead"}).status_code == 404

    created = client.post(
        "/mock/users", json={"username": "new", "email": "new@example.com"}
    ).json()["data"]
    assert created["username"] == "new"
    assert created["is_active"] is True
    assert created["issues_assigned"] == 0
    assert any(u["id"] == created["id"] for u in server.read_json("users.json")["users"])

    assert client.delete("/mock/users/u1").json() == {"data": None}
    ids = [u["id"] for u in server.read_json("users.json")["users"]]
    assert "u1" not in ids


# --------------------------------------------------------- organizations --


def test_organizations_crud_and_default_role_rename(client, data_dir):
    seed(
        "organizations.json",
        {
            "organizations": [
                {"id": "org-1", "name": "Acme", "defaultRole": "DEVELOPER"}
            ]
        },
    )

    assert len(client.get("/mock/organizations").json()["data"]) == 1
    assert client.get("/mock/organizations/org-1").json()["data"]["name"] == "Acme"
    assert client.get("/mock/organizations/nope").status_code == 404

    updated = client.patch(
        "/mock/organizations/org-1", json={"default_role": "LEAD"}
    ).json()["data"]
    assert updated["defaultRole"] == "LEAD"
    assert "default_role" not in updated
    assert updated["updatedAt"] > "2026"

    created = client.post("/mock/organizations", json={"name": "Beta"}).json()["data"]
    assert created["id"].startswith("org-")
    assert created["workspaces"][0]["id"] == "ws-default"
    assert created["quota"]["computeLimit"] == 500000

    assert client.delete("/mock/organizations/org-1").json() == {"data": None}
    remaining = [o["id"] for o in server.read_json("organizations.json")["organizations"]]
    assert "org-1" not in remaining


# ---------------------------------------------------------------- issues --


def test_issues_list_filters(client, data_dir):
    seed(
        "issues.json",
        {
            "issues": [
                issue("ISS-001", status="OPEN", priority="HIGH"),
                issue("ISS-002", status="BLOCKED", priority="LOW", project_id="other"),
                issue("ISS-003", status="OPEN", priority="CRITICAL"),
            ]
        },
    )

    res = client.get("/mock/issues").json()
    assert res["meta"]["total"] == 3

    assert client.get("/mock/issues", params={"status": "OPEN"}).json()["meta"]["total"] == 2
    assert (
        client.get("/mock/issues", params={"status": "OPEN,BLOCKED"}).json()["meta"]["total"]
        == 3
    )
    assert client.get("/mock/issues", params={"priority": "CRITICAL"}).json()["meta"]["total"] == 1
    assert client.get("/mock/issues", params={"project": "other"}).json()["meta"]["total"] == 1


def test_create_issue_auto_increments_id(client, data_dir):
    seed("issues.json", {"issues": [issue("ISS-001"), issue("ISS-007")]})

    created = client.post("/mock/issues", json={"title": "Nueva"}).json()["data"]
    assert created["id"] == "ISS-008"
    assert created["status"] == "OPEN"
    assert created["blocks"] == []
    assert created["agent_working"] is False
    assert created["created_at"].endswith("Z")


def test_create_issue_on_empty_store_starts_at_001(client, data_dir):
    seed("issues.json", {})

    created = client.post("/mock/issues", json={"title": "Primera"}).json()["data"]
    assert created["id"] == "ISS-001"


def test_update_and_delete_issue(client, data_dir):
    seed("issues.json", {"issues": [issue()]})

    updated = client.patch("/mock/issues/ISS-001", json={"status": "BLOCKED"}).json()["data"]
    assert updated["status"] == "BLOCKED"
    assert updated["updated_at"] > "2026"

    assert client.patch("/mock/issues/ISS-999", json={"status": "BLOCKED"}).status_code == 404
    assert client.delete("/mock/issues/ISS-999").status_code == 404

    assert client.delete("/mock/issues/ISS-001").json() == {"data": None}
    assert server.read_json("issues.json")["issues"] == []


# ------------------------------------------------------------ agent logs --


def test_agent_logs_empty_fallback(client, data_dir):
    seed("agent-logs.json", {})

    res = client.get("/mock/issues/ISS-001/agent-logs").json()["data"]
    assert res == {"issue_id": "ISS-001", "logs": []}

    seed("agent-logs.json", {"agent_logs": {"ISS-001": {"issue_id": "ISS-001", "logs": ["step"]}}})
    res = client.get("/mock/issues/ISS-001/agent-logs").json()["data"]
    assert res["logs"] == ["step"]


# ------------------------------------------------------------ components --


def test_components_crud(client, data_dir):
    seed("components.json", {"components": [{"id": "c1", "name": "Auth"}]})
    assert client.get("/mock/components").json()["data"][0]["id"] == "c1"

    created = client.post("/mock/components", json={"name": "Billing"}).json()["data"]
    assert created["alias"] == "BI"
    assert created["id"]

    updated = client.patch(
        "/mock/components/c1", json={"description": "auth module"}
    ).json()["data"]
    assert updated["description"] == "auth module"
    assert client.patch("/mock/components/nope", json={"description": "x"}).status_code == 404

    assert client.delete("/mock/components/c1").json() == {"data": None}
    assert client.delete("/mock/components/nope").status_code == 404


# -------------------------------------------------------------- policies --


def test_policies_crud(client, data_dir):
    seed("policies.json", {"policies": [{"id": "p1", "name": "Old"}]})
    assert client.get("/mock/policies").json()["data"][0]["name"] == "Old"

    created = client.post("/mock/policies", json={"name": "No cycles"}).json()["data"]
    assert created["rules"] == []
    assert created["is_active"] is True

    created_with_rule = client.post(
        "/mock/policies", json={"name": "Depth", "rule": "max_depth"}
    ).json()["data"]
    assert created_with_rule["rules"] == [{"type": "max_depth"}]

    patched = client.patch("/mock/policies/p1", json={"description": "d", "level": "HARD"}).json()["data"]
    assert patched["description"] == "d"
    assert patched["level"] == "HARD"
    assert client.patch("/mock/policies/nope", json={"description": "d"}).status_code == 404

    assert client.delete("/mock/policies/p1").json() == {"data": None}


# ----------------------------------------------------------- constraints --


def test_constraints_crud(client, data_dir):
    seed("constraints.json", {"constraints": [{"id": "CONST-001", "name": "Old"}]})

    created = client.post("/mock/constraints", json={"name": "No legacy"}).json()["data"]
    assert created["id"] == "CONST-002"
    assert created["is_active"] is True

    patched = client.patch(
        "/mock/constraints/CONST-001", json={"name": "Renamed", "severity": "HARD"}
    ).json()["data"]
    assert patched["name"] == "Renamed"
    assert patched["severity"] == "HARD"
    assert client.patch("/mock/constraints/nope", json={"name": "x"}).status_code == 404

    assert client.delete("/mock/constraints/CONST-001").json() == {"data": None}
    assert client.delete("/mock/constraints/nope").json() == {"data": None}


def test_validate_constraints_required_field(client, data_dir):
    seed(
        "constraints.json",
        {
            "constraints": [
                {
                    "id": "CONST-010",
                    "name": "Labels required",
                    "category": "ARCHITECTURE",
                    "severity": "HARD",
                    "is_active": True,
                    "rule": {"type": "required_field", "target_field": "labels", "min_count": 1},
                    "remediation": "add labels",
                },
                {
                    "id": "CONST-011",
                    "name": "Disabled",
                    "category": "ARCHITECTURE",
                    "severity": "HARD",
                    "is_active": False,
                    "rule": {"type": "required_field", "target_field": "title"},
                    "remediation": "n/a",
                },
            ]
        },
    )

    bad = client.post(
        "/mock/constraints/validate",
        json={"entity_type": "issue", "entity_data": {"title": "x"}},
    ).json()["data"]
    assert bad["valid"] is False
    assert bad["hard_violations"] == 1
    assert bad["checked_constraints"] == 1  # inactive skipped
    assert bad["violations"][0]["constraint_id"] == "CONST-010"

    good = client.post(
        "/mock/constraints/validate",
        json={"entity_type": "issue", "entity_data": {"title": "x", "labels": ["a"]}},
    ).json()["data"]
    assert good["valid"] is True
    assert good["total_violations"] == 0


def test_validate_constraints_detects_dependency_cycle(client, data_dir):
    seed(
        "constraints.json",
        {
            "constraints": [
                {
                    "id": "CONST-020",
                    "name": "No cycles",
                    "category": "DEPENDENCIES",
                    "severity": "HARD",
                    "is_active": True,
                    "rule": {"type": "no_cycles"},
                    "remediation": "break the cycle",
                }
            ]
        },
    )
    seed(
        "dependencies.json",
        {
            "dependencies": {
                "nodes": [{"id": "N1"}, {"id": "N2"}],
                "edges": [
                    {"from": "N1", "to": "N2", "type": "blocks"},
                    {"from": "N2", "to": "N1", "type": "blocks"},
                ],
            }
        },
    )
    seed("issues.json", {})

    res = client.post(
        "/mock/constraints/validate",
        json={"entity_type": "issue", "entity_data": {}},
    ).json()["data"]
    assert res["valid"] is False
    assert res["violations"][0]["message"] == "Circular dependency detected in the dependency graph"


def test_validate_constraints_max_depth(client, data_dir):
    seed(
        "constraints.json",
        {
            "constraints": [
                {
                    "id": "CONST-030",
                    "name": "Max depth",
                    "category": "DEPENDENCIES",
                    "severity": "SOFT",
                    "is_active": True,
                    "rule": {"type": "max_depth", "max_value": 8},
                    "remediation": "flatten",
                }
            ]
        },
    )
    seed("dependencies.json", {"dependencies": {"summary": {"critical_path_length": 12}}})
    seed("issues.json", {})

    res = client.post(
        "/mock/constraints/validate", json={"entity_type": "issue", "entity_data": {}}
    ).json()["data"]
    assert res["soft_violations"] == 1
    assert "exceeds maximum" in res["violations"][0]["message"]


# ------------------------------------------------------- dashboard/health --


def test_dashboard_stats_counts(client, data_dir):
    seed(
        "issues.json",
        {
            "issues": [
                issue("ISS-001", status="OPEN"),
                issue("ISS-002", status="BLOCKED"),
                issue("ISS-003", status="CLOSED"),
            ]
        },
    )
    seed("components.json", {"components": [{"id": "c1"}, {"id": "c2"}]})
    seed(
        "policies.json",
        {"policies": [{"id": "p1", "is_active": True}, {"id": "p2", "is_active": False}]},
    )

    stats = client.get("/mock/dashboard-stats").json()["data"]
    assert stats == {
        "total_issues": 3,
        "open_issues": 1,
        "in_progress_issues": 0,
        "blocked_issues": 1,
        "closed_issues": 1,
        "total_components": 2,
        "total_policies": 2,
        "active_policies": 1,
    }


def test_mock_health_metrics(client, data_dir):
    seed(
        "issues.json",
        {"issues": [issue("ISS-001", status="BLOCKED"), issue("ISS-002", status="OPEN")]},
    )
    seed(
        "users.json",
        {"users": [user("a1", type="agent", is_active=True), user("h1", type="human")]},
    )
    seed("components.json", {"components": [{"id": "c1"}]})
    seed(
        "constraints.json",
        {"constraints": [{"id": "k1", "is_active": True}, {"id": "k2", "is_active": False}]},
    )

    data = client.get("/mock/health").json()["data"]
    assert data["status"] == "healthy"
    assert set(data["services"]) == {"neo4j", "redis", "postgres", "api", "workers"}
    assert data["metrics"] == {
        "total_issues": 2,
        "blocked_issues": 1,
        "total_components": 1,
        "agents_working": 1,
        "total_users": 2,
        "total_constraints": 2,
        "active_constraints": 1,
    }


def test_sync_queue_shape(client):
    data = client.get("/mock/sync-queue").json()["data"]
    assert data["pending"] == 3
    assert len(data["queue"]) == 3
    assert data["github_connected"] is True


# ------------------------------------------------------------- analysis --


def test_analysis_impact_unknown_issue_404(client, data_dir):
    seed("issues.json", {"issues": [issue()]})
    seed("dependencies.json", {})

    assert client.get("/mock/analysis/impact/ISS-999").status_code == 404


def test_analysis_impact_returns_blast_radius(client, data_dir):
    seed(
        "issues.json",
        {
            "issues": [
                issue("ISS-001", title="Root", priority="HIGH"),
                issue("ISS-002", title="Child", status="OPEN"),
            ]
        },
    )
    seed(
        "dependencies.json",
        {"dependencies": {"edges": [{"from": "ISS-001", "to": "ISS-002", "type": "blocks"}]}},
    )

    data = client.get("/mock/analysis/impact/ISS-001").json()["data"]
    assert data["issue_id"] == "ISS-001"
    assert data["issue_title"] == "Root"
    assert data["total_affected"] == 1
    assert data["directly_affected"][0]["id"] == "ISS-002"
    assert data["graph_depth"] == 1
    assert data["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_root_cause_ranks_matching_closed_issue(client, data_dir):
    closed_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    seed(
        "issues.json",
        {
            "issues": [
                issue(
                    "ISS-050",
                    title="Login button crash on mobile",
                    status="CLOSED",
                    closed_at=closed_at,
                    labels=["login"],
                )
            ]
        },
    )
    seed("dependencies.json", {})

    res = client.post(
        "/mock/analysis/root-cause",
        json={
            "test_name": "test_login_button",
            "error_message": "login button crash",
            "labels": ["login"],
        },
    ).json()["data"]
    assert res[0]["issue_id"] == "ISS-050"
    assert res[0]["confidence"] > 0
    assert res[0]["reasons"]


def test_test_failures_endpoint(client, data_dir):
    seed("root-cause.json", {"test_failures": [{"test": "t1", "error": "boom"}]})
    assert client.get("/mock/test-failures").json()["data"] == [{"test": "t1", "error": "boom"}]


# ---------------------------------------------------------------- admin --


def test_admin_seed_and_reset(client, data_dir):
    seed("issues.json", {"issues": [issue()]})
    seed("users.json", {"users": [user()]})

    seeded = client.post("/mock/admin/seed", json={"seed_type": "minimal", "reset_first": True}).json()["data"]
    assert seeded["status"] == "success"
    assert seeded["seed_type"] == "minimal"
    assert seeded["reset_first"] is True
    assert server.read_json("issues.json") == {}

    seed("issues.json", {"issues": [issue()]})
    reset = client.post("/mock/admin/reset").json()["data"]
    assert reset["status"] == "success"
    assert server.read_json("issues.json") == {}
    assert client.get("/mock/issues").json()["data"] == []


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "ok"}
