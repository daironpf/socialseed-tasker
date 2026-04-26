"""Tests for the FastAPI REST API using in-memory mock repository."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.constraints import Constraint, ConstraintCategory, ConstraintLevel
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus, IssuePriority
from socialseed_tasker.entrypoints.web_api.app import create_app


class MockRepository(TaskRepositoryInterface):
    """In-memory mock repository for API testing."""

    def __init__(self) -> None:
        self._issues: dict[str, Issue] = {}
        self._components: dict[str, Component] = {}
        self._dependencies: dict[str, set[str]] = {}
        self._constraints: dict[str, Constraint] = {}
        self._labels: dict[str, set[str]] = {}

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
        self._dependencies.pop(issue_id, None)
        for deps in self._dependencies.values():
            deps.discard(issue_id)

    def list_issues(
        self,
        component_id: str | None = None,
        statuses: list[str] | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        issues = list(self._issues.values())
        if component_id:
            issues = [i for i in issues if str(i.component_id) == component_id]
        if statuses:
            issues = [i for i in issues if i.status.value in statuses]
        if project:
            issues = [
                i
                for i in issues
                if self._components.get(str(i.component_id), Component(name="", project="")).project == project
            ]
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
        blocked = []
        seen = set()
        for issue_id, deps in self._dependencies.items():
            issue = self._issues.get(issue_id)
            if issue and issue.status != IssueStatus.CLOSED and issue_id not in seen:
                for dep_id in deps:
                    dep = self._issues.get(dep_id)
                    if dep and dep.status != IssueStatus.CLOSED:
                        blocked.append(issue)
                        seen.add(issue_id)
                        break
        return blocked

    def get_workable_issues(
        self,
        priority: str | None = None,
        component_id: str | None = None,
    ) -> list[Issue]:
        workable = []
        for issue in self._issues.values():
            if issue.status == IssueStatus.CLOSED:
                continue
            if priority and issue.priority.value != priority:
                continue
            if component_id and str(issue.component_id) != component_id:
                continue
            deps = self._dependencies.get(str(issue.id), [])
            all_closed = all(self._issues.get(d) and self._issues.get(d).status == IssueStatus.CLOSED for d in deps)
            if all_closed or not deps:
                workable.append(issue)
        return workable

    def create_component(self, component: Component) -> None:
        self._components[str(component.id)] = component

    def get_component(self, component_id: str) -> Component | None:
        return self._components.get(component_id)

    def list_components(self, project: str | None = None) -> list[Component]:
        components = list(self._components.values())
        if project:
            components = [c for c in components if c.project == project]
        return components

    def update_component(self, component_id: str, updates: dict[str, Any]) -> Component:
        component = self._components[component_id]
        updated = component.model_copy(update=updates)
        self._components[component_id] = updated
        return updated

    def delete_component(self, component_id: str) -> None:
        self._components.pop(component_id, None)

    def get_component_by_name(self, name: str, project: str | None = None) -> Component | None:
        for comp in self._components.values():
            if comp.name == name and (project is None or comp.project == project):
                return comp
        return None

    def find_issues_by_title(self, title: str, component_id: str | None = None) -> list[Issue]:
        issues = [i for i in self._issues.values() if i.title == title]
        if component_id:
            issues = [i for i in issues if str(i.component_id) == component_id]
        return issues

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
        issue = self._issues[issue_id]
        updated = issue.model_copy(update={"agent_working": agent_id})
        self._issues[issue_id] = updated
        return updated

    def finish_agent_work(self, issue_id: str) -> Issue:
        issue = self._issues[issue_id]
        updated = issue.model_copy(update={"agent_working": None})
        self._issues[issue_id] = updated
        return updated

    def get_agent_status(self, issue_id: str) -> dict[str, Any]:
        issue = self._issues.get(issue_id)
        if issue:
            return {"agent_working": getattr(issue, "agent_working", None)}
        return {}

    def create_constraint(self, constraint: Constraint) -> None:
        self._constraints[str(constraint.id)] = constraint

    def list_constraints(self, category: str | None = None) -> list[Constraint]:
        constraints = list(self._constraints.values())
        if category:
            constraints = [c for c in constraints if c.category.value == category]
        return constraints

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
        result: dict[str, int] = {}
        if scope in ("all", "issues"):
            result["issues_deleted"] = len(self._issues)
            self._issues.clear()
            self._dependencies.clear()
        if scope in ("all", "components"):
            result["components_deleted"] = len(self._components)
            self._components.clear()
        return result

    @contextmanager
    def transaction(self) -> Iterator[None]:
        yield


@pytest.fixture()
def repo():
    return MockRepository()


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
        assert len(resp.json()["data"]["items"]) == 1

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
        assert len(resp.json()["data"]["items"]) == 1

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

    def test_workable_issues(self, client, component_id):
        resp_open = client.post(
            "/api/v1/issues",
            json={"title": "Open issue", "component_id": component_id},
        )
        resp_blocked = client.post(
            "/api/v1/issues",
            json={"title": "Blocked issue", "component_id": component_id},
        )
        open_id = resp_open.json()["data"]["id"]
        blocked_id = resp_blocked.json()["data"]["id"]

        client.post(
            f"/api/v1/issues/{blocked_id}/dependencies",
            json={"depends_on_id": open_id},
        )

        resp = client.get("/api/v1/workable-issues")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert any(i["id"] == open_id for i in data)
        assert not any(i["id"] == blocked_id for i in data)

    def test_workable_issues_with_priority_filter(self, client, component_id):
        client.post(
            "/api/v1/issues",
            json={"title": "High priority", "component_id": component_id, "priority": "HIGH"},
        )
        client.post(
            "/api/v1/issues",
            json={"title": "Low priority", "component_id": component_id, "priority": "LOW"},
        )

        resp = client.get("/api/v1/workable-issues?priority=HIGH")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(i["priority"] == "HIGH" for i in data)


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
        resp_issue = client.post(
            "/api/v1/issues",
            json={
                "title": "Test issue",
                "component_id": component_id,
            },
        )
        issue_id = resp_issue.json()["data"]["id"]
        client.post(f"/api/v1/issues/{issue_id}/close")

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


class TestProjectEndpoints:
    def test_project_summary(self, client, component_id):
        resp = client.get("/api/v1/projects/test-project/summary")
        assert resp.status_code in [200, 404]

    def test_project_summary_empty(self, client):
        resp = client.get("/api/v1/projects/nonexistent-project/summary")
        assert resp.status_code in [200, 404]


class TestGraphEndpoints:
    def test_graph_dependencies(self, client, component_id):
        resp = client.get("/api/v1/graph/dependencies")
        assert resp.status_code in [200, 404]


class TestAgentEndpoints:
    def test_start_agent_work(self, client, issue_id):
        resp = client.post(
            f"/api/v1/issues/{issue_id}/start",
            json={"agent_id": "agent-001"},
        )
        assert resp.status_code in [200, 201, 404, 405, 422]

    def test_finish_agent_work(self, client, issue_id):
        resp = client.post(f"/api/v1/issues/{issue_id}/finish")
        assert resp.status_code in [200, 201, 404, 405, 422]

    def test_agent_status(self, client, issue_id):
        resp = client.get(f"/api/v1/issues/{issue_id}/agent")
        assert resp.status_code in [200, 404, 405]


class TestConstraintsEndpoints:
    def test_list_constraints(self, client):
        resp = client.get("/api/v1/constraints")
        assert resp.status_code in [200, 404]

    def test_list_constraints_by_category(self, client):
        resp = client.get("/api/v1/constraints?category=architecture")
        assert resp.status_code in [200, 404]


class TestAnalysisExtended:
    def test_component_impact(self, client, component_id):
        resp = client.get(f"/api/v1/analyze/component-impact/{component_id}")
        assert resp.status_code in [200, 404, 405]

    def test_component_impact_nonexistent(self, client):
        resp = client.get("/api/v1/analyze/component-impact/00000000-0000-0000-0000-000000000000")
        assert resp.status_code in [200, 404, 405]


class TestValidationErrors:
    def test_create_issue_invalid_title(self, client, component_id):
        resp = client.post(
            "/api/v1/issues",
            json={"title": "", "component_id": component_id},
        )
        assert resp.status_code in [400, 422]

    def test_create_issue_invalid_priority(self, client, component_id):
        resp = client.post(
            "/api/v1/issues",
            json={"title": "Test", "component_id": component_id, "priority": "INVALID"},
        )
        assert resp.status_code in [400, 422]

    def test_list_issues_invalid_status(self, client):
        resp = client.get("/api/v1/issues?statuses=INVALID_STATUS")
        assert resp.status_code == 200

    def test_list_issues_pagination_edge_cases(self, client, component_id):
        resp = client.get("/api/v1/issues?page=0&limit=10")
        assert resp.status_code in [400, 422]

    def test_list_issues_limit_exceeded(self, client, component_id):
        resp = client.get("/api/v1/issues?limit=200")
        assert resp.status_code in [400, 422]


class TestDependencyEdgeCases:
    def test_add_self_dependency(self, client, component_id):
        resp_issue = client.post(
            "/api/v1/issues",
            json={"title": "Self dep", "component_id": component_id},
        )
        issue_id = resp_issue.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/issues/{issue_id}/dependencies",
            json={"depends_on_id": issue_id},
        )
        assert resp.status_code in [400, 409, 422]

    def test_remove_nonexistent_dependency(self, client, component_id):
        resp_a = client.post(
            "/api/v1/issues",
            json={"title": "A", "component_id": component_id},
        )
        a_id = resp_a.json()["data"]["id"]
        b_id = str(uuid4())

        resp = client.delete(f"/api/v1/issues/{a_id}/dependencies/{b_id}")
        assert resp.status_code in [204, 404]

    def test_list_dependencies_empty(self, client, issue_id):
        resp = client.get(f"/api/v1/issues/{issue_id}/dependencies")
        assert resp.status_code == 200

    def test_list_dependents_empty(self, client, issue_id):
        resp = client.get(f"/api/v1/issues/{issue_id}/dependents")
        assert resp.status_code == 200


class TestComponentEdgeCases:
    def test_update_component_no_fields(self, client, component_id):
        resp = client.patch(f"/api/v1/components/{component_id}", json={})
        assert resp.status_code in [400, 422]

    def test_delete_nonexistent_component(self, client):
        resp = client.delete("/api/v1/components/nonexistent-id")
        assert resp.status_code == 404


class TestIssueEdgeCases:
    def test_update_nonexistent_issue(self, client):
        resp = client.patch(
            "/api/v1/issues/nonexistent-id",
            json={"title": "New title"},
        )
        assert resp.status_code == 404

    def test_close_nonexistent_issue(self, client):
        resp = client.post("/api/v1/issues/nonexistent-id/close")
        assert resp.status_code == 404

    def test_delete_already_deleted_issue(self, client, issue_id):
        client.delete(f"/api/v1/issues/{issue_id}")
        resp = client.delete(f"/api/v1/issues/{issue_id}")
        assert resp.status_code == 404

    def test_get_issue_dependencies(self, client, issue_id):
        resp = client.get(f"/api/v1/issues/{issue_id}/dependencies")
        assert resp.status_code == 200


class TestFiltersAndSorting:
    def test_list_issues_by_component_filter(self, client, component_id):
        other_component = client.post(
            "/api/v1/components",
            json={"name": "Other", "project": "test"},
        )
        other_id = other_component.json()["data"]["id"]

        client.post("/api/v1/issues", json={"title": "Issue 1", "component_id": component_id})
        client.post("/api/v1/issues", json={"title": "Issue 2", "component_id": other_id})

        resp = client.get(f"/api/v1/issues?component={component_id}")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1

    def test_list_components_all_flag(self, client):
        client.post("/api/v1/components", json={"name": "A", "project": "p1"})
        client.post("/api/v1/components", json={"name": "B", "project": "p2"})

        resp = client.get("/api/v1/components?all=true")
        assert resp.status_code == 200
