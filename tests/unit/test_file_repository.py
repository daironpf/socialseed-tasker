"""Tests for the file-based task repository."""

import tempfile
from pathlib import Path

import pytest

from socialseed_tasker.core.task_management.entities import (
    Component,
    Issue,
    IssueStatus,
)
from socialseed_tasker.storage.local_files.repositories import FileTaskRepository


@pytest.fixture()
def repo() -> FileTaskRepository:
    tmp = Path(tempfile.mkdtemp())
    return FileTaskRepository(tmp)


class TestFileTaskRepository:
    # -- Component CRUD ------------------------------------------------------

    def test_create_and_get_component(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        retrieved = repo.get_component(str(comp.id))
        assert retrieved is not None
        assert retrieved.id == comp.id
        assert retrieved.name == "Backend"

    def test_get_missing_component_returns_none(self, repo: FileTaskRepository):
        assert repo.get_component("nonexistent") is None

    def test_list_components(self, repo: FileTaskRepository):
        c1 = Component(name="A", project="proj1")
        c2 = Component(name="B", project="proj1")
        c3 = Component(name="C", project="proj2")
        repo.create_component(c1)
        repo.create_component(c2)
        repo.create_component(c3)

        all_comps = repo.list_components()
        assert len(all_comps) == 3

        proj1 = repo.list_components(project="proj1")
        assert len(proj1) == 2

    # -- Issue CRUD ----------------------------------------------------------

    def test_create_and_get_issue(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        issue = Issue(title="Test issue", component_id=comp.id)
        repo.create_issue(issue)

        retrieved = repo.get_issue(str(issue.id))
        assert retrieved is not None
        assert retrieved.title == "Test issue"

    def test_get_missing_issue_returns_none(self, repo: FileTaskRepository):
        assert repo.get_issue("nonexistent") is None

    def test_update_issue(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        issue = Issue(title="Original", component_id=comp.id)
        repo.create_issue(issue)

        updated = repo.update_issue(str(issue.id), {"title": "Updated"})
        assert updated.title == "Updated"

    def test_close_issue(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        issue = Issue(title="Test", component_id=comp.id)
        repo.create_issue(issue)

        closed = repo.close_issue(str(issue.id))
        assert closed.status == IssueStatus.CLOSED
        assert closed.closed_at is not None

    def test_delete_issue(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        issue = Issue(title="Test", component_id=comp.id)
        repo.create_issue(issue)

        repo.delete_issue(str(issue.id))
        assert repo.get_issue(str(issue.id)) is None

    def test_list_issues(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        i1 = Issue(title="A", component_id=comp.id)
        i2 = Issue(title="B", component_id=comp.id)
        repo.create_issue(i1)
        repo.create_issue(i2)

        all_issues = repo.list_issues()
        assert len(all_issues) == 2

    def test_list_issues_filter_by_status(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        i1 = Issue(title="Open", component_id=comp.id)
        i2 = Issue(title="Closed", component_id=comp.id)
        repo.create_issue(i1)
        repo.create_issue(i2)
        repo.close_issue(str(i2.id))

        open_issues = repo.list_issues(status=IssueStatus.OPEN)
        assert len(open_issues) == 1
        assert open_issues[0].id == i1.id

    # -- Dependency management -----------------------------------------------

    def test_add_and_get_dependencies(self, repo: FileTaskRepository):
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

    def test_get_dependents(self, repo: FileTaskRepository):
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

    def test_remove_dependency(self, repo: FileTaskRepository):
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

    def test_delete_issue_removes_relationships(self, repo: FileTaskRepository):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)
        a = Issue(title="A", component_id=comp.id)
        b = Issue(title="B", component_id=comp.id)
        repo.create_issue(a)
        repo.create_issue(b)

        repo.add_dependency(str(a.id), str(b.id))
        repo.delete_issue(str(a.id))

        assert len(list(repo._relationships_dir.glob("*.json"))) == 0
