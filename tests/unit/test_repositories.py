"""Unit tests for repositories using FakeNeo4jDriver."""

from __future__ import annotations

from uuid import uuid4

import pytest

from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus, IssuePriority
from socialseed_tasker.storage.graph_database.driver import Neo4jDriver
from socialseed_tasker.storage.graph_database.repositories import Neo4jTaskRepository
from tests.fakes.fake_neo4j_driver import FakeNeo4jDriver


@pytest.fixture
def fake_driver():
    """Create a FakeNeo4jDriver with test data."""
    driver = FakeNeo4jDriver()
    driver.setup_component("11111111-1111-1111-1111-111111111111", "Backend", "test-project", "Backend service")
    driver.setup_component("22222222-2222-2222-2222-222222222222", "Frontend", "test-project", "Frontend service")
    driver.setup_issue(
        "33333333-3333-3333-3333-333333333333",
        "Implement login",
        "11111111-1111-1111-1111-111111111111",
        status="OPEN",
        priority="HIGH",
        description="Add login functionality",
        labels=["auth"],
    )
    driver.setup_issue(
        "44444444-4444-4444-4444-444444444444",
        "Fix header bug",
        "11111111-1111-1111-1111-111111111111",
        status="OPEN",
        priority="MEDIUM",
    )
    driver.setup_issue(
        "55555555-5555-5555-5555-555555555555",
        "Add styles",
        "22222222-2222-2222-2222-222222222222",
        status="OPEN",
        priority="LOW",
    )
    driver.add_dependency("33333333-3333-3333-3333-333333333333", "44444444-4444-4444-4444-444444444444")
    return driver


@pytest.fixture
def repo(fake_driver):
    """Create a repository with FakeNeo4jDriver."""
    return Neo4jTaskRepository(fake_driver)


class TestNeo4jDriverFake:
    """Tests for the FakeNeo4jDriver."""

    def test_driver_properties(self, fake_driver):
        assert fake_driver.uri == "bolt://fake:7687"
        assert fake_driver.database == "neo4j"
        assert fake_driver.health_check() is True
        assert fake_driver.verify_connectivity() is True

    def test_session_context_manager(self, fake_driver):
        with fake_driver.session() as session:
            result = session.run("RETURN 1 AS ok")
            assert result.single()["ok"] == 1

    def test_add_node(self, fake_driver):
        node_id = fake_driver.add_node("Test", {"id": "66666666-6666-6666-6666-666666666666", "name": "test"})
        assert node_id == "66666666-6666-6666-6666-666666666666"
        assert fake_driver.get_node("66666666-6666-6666-6666-666666666666")["name"] == "test"

    def test_get_node(self, fake_driver):
        node = fake_driver.get_node("11111111-1111-1111-1111-111111111111")
        assert node is not None
        assert node["name"] == "Backend"

    def test_get_nodes_by_label(self, fake_driver):
        issues = fake_driver.get_nodes_by_label("Issue")
        assert len(issues) == 3

    def test_clear(self, fake_driver):
        fake_driver.clear()
        assert len(fake_driver._nodes) == 0
        assert len(fake_driver._relationships) == 0


class TestIssueRepositoryWithFake:
    """Tests for IssueRepository using FakeNeo4jDriver."""

    def test_get_issue(self, repo):
        issue = repo.get_issue("33333333-3333-3333-3333-333333333333")
        assert issue is not None
        assert issue.title == "Implement login"
        assert issue.status == IssueStatus.OPEN

    def test_get_missing_issue(self, repo):
        issue = repo.get_issue("00000000-0000-0000-0000-000000000000")
        assert issue is None

    def test_list_issues(self, repo):
        issues = repo.list_issues()
        assert len(issues) == 3

    def test_list_issues_by_status(self, repo):
        issues = repo.list_issues(status=IssueStatus.OPEN)
        assert len(issues) == 3

    def test_list_issues_by_component(self, repo):
        issues = repo.list_issues(component_id="11111111-1111-1111-1111-111111111111")
        assert len(issues) == 2

    def test_get_dependencies(self, repo):
        deps = repo.get_dependencies("33333333-3333-3333-3333-333333333333")
        assert len(deps) == 1
        assert str(deps[0].id) == "44444444-4444-4444-4444-444444444444"

    def test_get_blocked_issues(self, repo):
        blocked = repo.get_blocked_issues()
        assert len(blocked) == 1
        assert str(blocked[0].id) == "33333333-3333-3333-3333-333333333333"


class TestComponentRepositoryWithFake:
    """Tests for ComponentRepository using FakeNeo4jDriver."""

    def test_get_component(self, repo):
        comp = repo.get_component("11111111-1111-1111-1111-111111111111")
        assert comp is not None
        assert comp.name == "Backend"

    def test_get_missing_component(self, repo):
        comp = repo.get_component("00000000-0000-0000-0000-000000000000")
        assert comp is None

    def test_list_components(self, repo):
        components = repo.list_components()
        assert len(components) == 2

    def test_list_components_by_project(self, repo):
        components = repo.list_components(project="test-project")
        assert len(components) == 2

    def test_get_component_by_name(self, repo):
        comp = repo.get_component_by_name("Backend")
        assert comp is not None
        assert comp.name == "Backend"