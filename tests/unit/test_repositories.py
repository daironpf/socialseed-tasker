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
    driver.setup_component("comp-1", "Backend", "test-project", "Backend service")
    driver.setup_component("comp-2", "Frontend", "test-project", "Frontend service")
    driver.setup_issue(
        "issue-1",
        "Implement login",
        "comp-1",
        status="OPEN",
        priority="HIGH",
        description="Add login functionality",
        labels=["auth"],
    )
    driver.setup_issue(
        "issue-2",
        "Fix header bug",
        "comp-1",
        status="OPEN",
        priority="MEDIUM",
    )
    driver.setup_issue(
        "issue-3",
        "Add styles",
        "comp-2",
        status="OPEN",
        priority="LOW",
    )
    driver.add_dependency("issue-1", "issue-2")
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
        node_id = fake_driver.add_node("Test", {"id": "test-1", "name": "test"})
        assert node_id == "test-1"
        assert fake_driver.get_node("test-1")["name"] == "test"

    def test_get_node(self, fake_driver):
        node = fake_driver.get_node("comp-1")
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
        issue = repo.get_issue("issue-1")
        assert issue is not None
        assert issue.title == "Implement login"
        assert issue.status == IssueStatus.OPEN

    def test_get_missing_issue(self, repo):
        issue = repo.get_issue("nonexistent")
        assert issue is None

    def test_list_issues(self, repo):
        issues = repo.list_issues()
        assert len(issues) == 3

    def test_list_issues_by_status(self, repo):
        issues = repo.list_issues(status=IssueStatus.OPEN)
        assert len(issues) == 3

    def test_list_issues_by_component(self, repo):
        issues = repo.list_issues(component_id="comp-1")
        assert len(issues) == 2

    def test_get_dependencies(self, repo):
        deps = repo.get_dependencies("issue-1")
        assert len(deps) == 1
        assert str(deps[0].id) == "issue-2"

    def test_get_blocked_issues(self, repo):
        blocked = repo.get_blocked_issues()
        assert len(blocked) == 1
        assert str(blocked[0].id) == "issue-1"


class TestComponentRepositoryWithFake:
    """Tests for ComponentRepository using FakeNeo4jDriver."""

    def test_get_component(self, repo):
        comp = repo.get_component("comp-1")
        assert comp is not None
        assert comp.name == "Backend"

    def test_get_missing_component(self, repo):
        comp = repo.get_component("nonexistent")
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