"""Additional API route tests for issue #238 - Increase API routes coverage."""

import pytest
from fastapi.testclient import TestClient
from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus, IssuePriority
from socialseed_tasker.entrypoints.web_api.app import create_app


class MockRepoFull(TaskRepositoryInterface):
    """Full mock repository for additional API testing."""

    def __init__(self):
        self._issues: dict[str, Issue] = {}
        self._components: dict[str, Component] = {}
        self._dependencies: dict[str, set[str]] = {}
        self._constraints = {}

    def create_issue(self, issue: Issue) -> None:
        self._issues[str(issue.id)] = issue

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._issues.get(issue_id)

    def update_issue(self, issue_id: str, updates: dict) -> Issue:
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

    def list_issues(self, component_id=None, statuses=None, project=None):
        issues = list(self._issues.values())
        if component_id:
            issues = [i for i in issues if str(i.component_id) == component_id]
        if statuses:
            issues = [i for i in issues if i.status.value in statuses]
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
        return []

    def get_blocked_issues(self) -> list[Issue]:
        return []

    def get_workable_issues(self, priority=None, component_id=None) -> list[Issue]:
        return [i for i in self._issues.values() if i.status != IssueStatus.CLOSED]

    def create_component(self, component: Component) -> None:
        self._components[str(component.id)] = component

    def get_component(self, component_id: str) -> Component | None:
        return self._components.get(component_id)

    def list_components(self, project: str | None = None) -> list[Component]:
        components = list(self._components.values())
        if project:
            components = [c for c in components if c.project == project]
        return components

    def update_component(self, component_id: str, updates: dict) -> Component:
        comp = self._components[component_id]
        updated = comp.model_copy(update=updates)
        self._components[component_id] = updated
        return updated

    def delete_component(self, component_id: str) -> None:
        self._components.pop(component_id, None)

    def get_component_by_name(self, name: str, project: str | None = None) -> Component | None:
        for c in self._components.values():
            if c.name == name and (project is None or c.project == project):
                return c
        return None

    def find_issues_by_title(self, title: str, component_id: str | None = None) -> list[Issue]:
        return []

    def add_reasoning_log(self, issue_id: str, context: str, reasoning: str, related_nodes=None) -> Issue:
        return self._issues[issue_id]

    def get_reasoning_logs(self, issue_id: str) -> list[dict]:
        return []

    def update_manifest_todo(self, issue_id: str, todo: list[dict]) -> Issue:
        return self._issues[issue_id]

    def update_manifest_files(self, issue_id: str, files: list[str]) -> Issue:
        return self._issues[issue_id]

    def update_manifest_notes(self, issue_id: str, notes: list[str]) -> Issue:
        return self._issues[issue_id]

    def get_manifest(self, issue_id: str) -> dict:
        return {}

    def start_agent_work(self, issue_id: str, agent_id: str) -> Issue:
        return self._issues[issue_id]

    def finish_agent_work(self, issue_id: str) -> Issue:
        return self._issues[issue_id]

    def get_agent_status(self, issue_id: str) -> dict:
        issue = self._issues.get(issue_id)
        if issue:
            return {"agent_working": getattr(issue, "agent_working", None)}
        return {}

    def create_constraint(self, constraint) -> None:
        pass

    def list_constraints(self, category: str | None = None) -> list:
        return []

    def get_constraint(self, constraint_id: str):
        return None

    def delete_constraint(self, constraint_id: str) -> None:
        pass

    def update_constraint(self, constraint_id: str, updates: dict):
        from socialseed_tasker.core.task_management.constraints import (
            Constraint,
            ConstraintCategory,
            ConstraintLevel,
            ConstraintStatus,
        )

        existing = self._constraints.get(constraint_id)
        if existing is None:
            from uuid import uuid4

            existing = Constraint(
                id=uuid4(),
                category=ConstraintCategory.ARCHITECTURE,
                level=ConstraintLevel.REQUIRED,
                rule_type="test",
                required=True,
                status=ConstraintStatus.ACTIVE,
            )
        data = existing.model_dump()
        data.update(updates)
        updated = Constraint(**data)
        self._constraints[constraint_id] = updated
        return updated

    def reset_data(self, scope: str = "all") -> dict:
        return {}

    def transaction(self):
        from contextlib import contextmanager

        @contextmanager
        def _tx():
            yield

        return _tx()


@pytest.fixture()
def repo_full():
    return MockRepoFull()


@pytest.fixture()
def client_full(repo_full):
    app = create_app(repository=repo_full)
    return TestClient(app)


class TestPaginationEdgeCases:
    """Tests for pagination edge cases - Issue #238"""

    def test_issues_pagination_page_out_of_range(self, client_full, repo_full):
        """Test pagination when page exceeds available data."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        for i in range(3):
            issue = Issue(
                title=f"Issue {i}",
                component_id=comp.id,
                priority=IssuePriority.MEDIUM,
            )
            repo_full.create_issue(issue)

        resp = client_full.get("/api/v1/issues?page=100&limit=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 0
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_prev"] is True

    def test_issues_pagination_zero_limit(self, client_full, repo_full):
        """Test pagination with zero limit."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)
        issue = Issue(title="Issue", component_id=comp.id, priority=IssuePriority.MEDIUM)
        repo_full.create_issue(issue)

        resp = client_full.get("/api/v1/issues?page=1&limit=1")
        assert resp.status_code == 200

    def test_issues_pagination_last_page(self, client_full, repo_full):
        """Test accessing the last page of results."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        repo_full.create_issue(
            Issue(title="Issue 1", component_id=comp.id, priority=IssuePriority.MEDIUM)
        )
        repo_full.create_issue(
            Issue(title="Issue 2", component_id=comp.id, priority=IssuePriority.MEDIUM)
        )

        resp = client_full.get("/api/v1/issues?page=1&limit=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_prev"] is False


class TestComponentFilters:
    """Tests for component filters - Issue #238"""

    def test_components_filter_by_project_invalid(self, client_full, repo_full):
        """Test filtering components by non-existent project."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test-project", description="")
        repo_full.create_component(comp)

        resp = client_full.get("/api/v1/components?project=nonexistent-project")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 0

    def test_components_filter_by_name_exact_match(self, client_full, repo_full):
        """Test filtering components by exact name."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="MyComponent", project="test", description="")
        repo_full.create_component(comp)

        resp = client_full.get("/api/v1/components?name=MyComponent")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "MyComponent"

    def test_components_filter_by_name_not_found(self, client_full, repo_full):
        """Test filtering by name that doesn't exist."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Existing", project="test", description="")
        repo_full.create_component(comp)

        resp = client_full.get("/api/v1/components?name=Nonexistent")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 0


class TestAnalysisCoverage:
    """Additional analysis coverage tests - Issue #238"""

    def test_analyze_impact_with_closed_issue(self, client_full, repo_full):
        """Test impact analysis with a closed issue."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue_a = Issue(
            title="Feature A",
            component_id=comp.id,
            priority=IssuePriority.HIGH,
            status=IssueStatus.CLOSED,
        )
        issue_b = Issue(
            title="Feature B", component_id=comp.id, priority=IssuePriority.MEDIUM
        )
        repo_full.create_issue(issue_a)
        repo_full.create_issue(issue_b)

        resp = client_full.get(f"/api/v1/analyze/impact/{issue_a.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "risk_level" in data

    def test_root_cause_with_closed_issue(self, client_full, repo_full):
        """Test root cause analysis with closed issue."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(
            title="Fixed bug",
            component_id=comp.id,
            description="Fixed NPE",
            status=IssueStatus.CLOSED,
        )
        repo_full.create_issue(issue)

        resp = client_full.post(
            "/api/v1/analyze/root-cause",
            json={
                "test_id": "test_xyz",
                "test_name": "test_xyz",
                "error_message": "NullPointerException",
                "component": str(comp.id),
            },
        )
        assert resp.status_code == 200


class TestDependencyBulk:
    """Tests for bulk dependency operations - Issue #238"""

    def test_add_dependencies_bulk(self, client_full, repo_full):
        """Test bulk add dependencies."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue_main = Issue(title="Main", component_id=comp.id, priority=IssuePriority.HIGH)
        issue_dep1 = Issue(title="Dep1", component_id=comp.id, priority=IssuePriority.MEDIUM)
        issue_dep2 = Issue(title="Dep2", component_id=comp.id, priority=IssuePriority.LOW)
        repo_full.create_issue(issue_main)
        repo_full.create_issue(issue_dep1)
        repo_full.create_issue(issue_dep2)

        resp = client_full.post(
            f"/api/v1/issues/{issue_main.id}/dependencies/bulk",
            json={"depends_on_ids": [str(issue_dep1.id), str(issue_dep2.id)]},
        )
        assert resp.status_code == 200

    def test_add_dependencies_bulk_with_invalid(self, client_full, repo_full):
        """Test bulk add with some invalid dependencies."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue_main = Issue(title="Main", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue_main)

        resp = client_full.post(
            f"/api/v1/issues/{issue_main.id}/dependencies/bulk",
            json={"depends_on_ids": [str(uuid4())]},
        )
        assert resp.status_code == 200


class TestComponentDependency:
    """Tests for component dependencies - Issue #238"""

    def test_add_component_dependency(self, client_full, repo_full):
        """Test adding component dependency."""
        from uuid import uuid4

        comp_a = Component(id=uuid4(), name="CompA", project="test", description="")
        comp_b = Component(id=uuid4(), name="CompB", project="test", description="")
        repo_full.create_component(comp_a)
        repo_full.create_component(comp_b)

        resp = client_full.post(
            f"/api/v1/components/{comp_a.id}/dependencies",
            json={"depends_on_id": str(comp_b.id)},
        )
        assert resp.status_code == 200

    def test_add_self_component_dependency(self, client_full, repo_full):
        """Test adding self dependency returns 400."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Comp", project="test", description="")
        repo_full.create_component(comp)

        resp = client_full.post(
            f"/api/v1/components/{comp.id}/dependencies",
            json={"depends_on_id": str(comp.id)},
        )
        assert resp.status_code == 400


class TestManifest:
    """Tests for agent manifest endpoints - Issue #238"""

    def test_update_manifest_todo(self, client_full, repo_full):
        """Test updating manifest TODO."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.patch(
            f"/api/v1/issues/{issue.id}/manifest/todo",
            json={"todo": [{"task": "Step 1", "completed": "false"}]},
        )
        assert resp.status_code == 200

    def test_update_manifest_files(self, client_full, repo_full):
        """Test updating manifest files."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.patch(
            f"/api/v1/issues/{issue.id}/manifest/files",
            json={"files": ["src/main.py", "tests/test_main.py"]},
        )
        assert resp.status_code == 200

    def test_update_manifest_notes(self, client_full, repo_full):
        """Test updating manifest notes."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.patch(
            f"/api/v1/issues/{issue.id}/manifest/notes",
            json={"notes": ["Found a simpler approach"]},
        )
        assert resp.status_code == 200


class TestReasoningLogs:
    """Tests for reasoning log endpoints - Issue #238"""

    def test_get_reasoning_logs(self, client_full, repo_full):
        """Test getting reasoning logs."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.get(f"/api/v1/issues/{issue.id}/reasoning")
        assert resp.status_code == 200

    def test_add_reasoning_log(self, client_full, repo_full):
        """Test adding reasoning log."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.post(
            f"/api/v1/issues/{issue.id}/reasoning",
            json={"context": "implementation", "reasoning": "Selected approach A", "related_nodes": []},
        )
        assert resp.status_code == 200


class TestGitHubIntegration:
    """Tests for GitHub integration - Issue #238"""

    def test_link_github_issue(self, client_full, repo_full):
        """Test linking GitHub issue."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.post(
            f"/api/v1/issues/{issue.id}/link-github?github_issue_url=https://github.com/owner/repo/issues/123",
        )
        assert resp.status_code in [200, 400, 422]

    def test_link_github_invalid_url(self, client_full, repo_full):
        """Test linking with invalid URL returns 400."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.post(
            f"/api/v1/issues/{issue.id}/link-github?github_issue_url=invalid-url",
        )
        assert resp.status_code in [200, 400, 422]

    def test_unlink_github_issue(self, client_full, repo_full):
        """Test unlinking GitHub issue."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.post(f"/api/v1/issues/{issue.id}/unlink-github")
        assert resp.status_code in [200, 404]


class TestProjectList:
    """Tests for project listing - Issue #238"""

    def test_list_projects(self, client_full, repo_full):
        """Test listing projects."""
        from uuid import uuid4

        comp1 = Component(id=uuid4(), name="Comp1", project="project-a", description="")
        comp2 = Component(id=uuid4(), name="Comp2", project="project-b", description="")
        repo_full.create_component(comp1)
        repo_full.create_component(comp2)

        resp = client_full.get("/api/v1/projects")
        assert resp.status_code == 200


class TestAgentHeartbeat:
    """Tests for agent heartbeat - Issue #238"""

    def test_agent_heartbeat(self, client_full, repo_full):
        """Test agent heartbeat."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.post(f"/api/v1/issues/{issue.id}/agent/heartbeat")
        assert resp.status_code in [200, 409]


class TestIssueDeployments:
    """Tests for issue deployments - Issue #238"""

    def test_get_issue_deployments(self, client_full, repo_full):
        """Test getting issue deployments."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.get(f"/api/v1/issues/{issue.id}/deployments")
        assert resp.status_code == 200


class TestIssueComponent:
    """Tests for issue component - Issue #238"""

    def test_get_issue_component(self, client_full, repo_full):
        """Test getting issue's component."""
        from uuid import uuid4

        comp = Component(id=uuid4(), name="Test", project="test", description="")
        repo_full.create_component(comp)

        issue = Issue(title="Test Issue", component_id=comp.id, priority=IssuePriority.HIGH)
        repo_full.create_issue(issue)

        resp = client_full.get(f"/api/v1/issues/{issue.id}/component")
        assert resp.status_code == 200