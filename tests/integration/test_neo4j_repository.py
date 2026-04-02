"""Integration tests for the Neo4j graph database repository.

These tests require a running Neo4j instance (via docker compose).
Run with: pytest tests/integration/test_neo4j_repository.py -v
"""

import os

import pytest

from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.storage.graph_database.driver import Neo4jDriver
from socialseed_tasker.storage.graph_database.repositories import Neo4jTaskRepository

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "tasker_password")


@pytest.fixture(scope="module")
def driver():
    d = Neo4jDriver(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    d.connect()
    yield d
    d.close()


@pytest.fixture()
def repo(driver):
    r = Neo4jTaskRepository(driver)
    yield r
    _cleanup(driver)


def _cleanup(driver):
    with driver.driver.session(database=driver.database) as session:
        session.run("MATCH (n) DETACH DELETE n")


class TestNeo4jDriver:
    def test_connect_and_health_check(self, driver):
        assert driver.health_check() is True


class TestNeo4jComponentRepository:
    def test_create_and_get_component(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        retrieved = repo.get_component(str(comp.id))
        assert retrieved is not None
        assert retrieved.id == comp.id
        assert retrieved.name == "Backend"

    def test_get_missing_component_returns_none(self, repo):
        result = repo.get_component("nonexistent")
        assert result is None

    def test_list_components(self, repo):
        c1 = Component(name="A", project="proj")
        c2 = Component(name="B", project="proj")
        repo.create_component(c1)
        repo.create_component(c2)

        all_comps = repo.list_components()
        assert len(all_comps) >= 2

        filtered = repo.list_components(project="proj")
        assert len(filtered) >= 2


class TestNeo4jIssueRepository:
    def test_create_and_get_issue(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)

        issue = Issue(title="Test issue", component_id=comp.id)
        repo.create_issue(issue)

        retrieved = repo.get_issue(str(issue.id))
        assert retrieved is not None
        assert retrieved.title == "Test issue"

    def test_get_missing_issue_returns_none(self, repo):
        result = repo.get_issue("nonexistent")
        assert result is None

    def test_update_issue(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        issue = Issue(title="Original", component_id=comp.id)
        repo.create_issue(issue)

        updated = repo.update_issue(str(issue.id), {"title": "Updated"})
        assert updated.title == "Updated"

    def test_close_issue(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        issue = Issue(title="Test", component_id=comp.id)
        repo.create_issue(issue)

        closed = repo.close_issue(str(issue.id))
        assert closed.status == IssueStatus.CLOSED
        assert closed.closed_at is not None

    def test_delete_issue(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        issue = Issue(title="Test", component_id=comp.id)
        repo.create_issue(issue)

        repo.delete_issue(str(issue.id))
        result = repo.get_issue(str(issue.id))
        assert result is None

    def test_list_issues(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        i1 = Issue(title="A", component_id=comp.id)
        i2 = Issue(title="B", component_id=comp.id)
        repo.create_issue(i1)
        repo.create_issue(i2)

        all_issues = repo.list_issues()
        assert len(all_issues) >= 2

    def test_list_issues_filter_by_status(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        i1 = Issue(title="Open", component_id=comp.id)
        i2 = Issue(title="Closed", component_id=comp.id)
        repo.create_issue(i1)
        repo.create_issue(i2)
        repo.close_issue(str(i2.id))

        open_issues = repo.list_issues(status=IssueStatus.OPEN)
        assert len(open_issues) >= 1


class TestNeo4jDependencyManagement:
    def test_add_and_get_dependencies(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        a = Issue(title="A", component_id=comp.id)
        b = Issue(title="B", component_id=comp.id)
        repo.create_issue(a)
        repo.create_issue(b)

        repo.add_dependency(str(a.id), str(b.id))
        deps = repo.get_dependencies(str(a.id))
        assert len(deps) == 1
        assert deps[0].id == b.id

    def test_get_dependents(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        a = Issue(title="A", component_id=comp.id)
        b = Issue(title="B", component_id=comp.id)
        repo.create_issue(a)
        repo.create_issue(b)

        repo.add_dependency(str(a.id), str(b.id))
        dependents = repo.get_dependents(str(b.id))
        assert len(dependents) == 1
        assert dependents[0].id == a.id

    def test_remove_dependency(self, repo, driver):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        a = Issue(title="A", component_id=comp.id)
        b = Issue(title="B", component_id=comp.id)
        repo.create_issue(a)
        repo.create_issue(b)

        repo.add_dependency(str(a.id), str(b.id))
        repo.remove_dependency(str(a.id), str(b.id))
        deps = repo.get_dependencies(str(a.id))
        assert len(deps) == 0
