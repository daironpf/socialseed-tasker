"""Tests for core domain actions."""

from uuid import UUID

import pytest

from socialseed_tasker.core.task_management.actions import (
    CircularDependencyError,
    ComponentNotFoundError,
    IssueAlreadyClosedError,
    IssueNotFoundError,
    OpenDependenciesError,
    add_dependency_action,
    close_issue_action,
    create_issue_action,
    get_blocked_issues_action,
    get_dependency_chain_action,
    move_issue_action,
    remove_dependency_action,
)
from socialseed_tasker.core.task_management.entities import (
    Component,
    Issue,
    IssueStatus,
)


class FakeRepository:
    """In-memory implementation of TaskRepositoryInterface for testing."""

    def __init__(self) -> None:
        self._issues: dict[str, Issue] = {}
        self._components: dict[str, Component] = {}
        self._dependencies: dict[str, set[str]] = {}

    def _key(self, id_value: str | UUID) -> str:
        return str(id_value)

    # -- Issue CRUD ----------------------------------------------------------

    def create_issue(self, issue: Issue) -> None:
        key = self._key(issue.id)
        self._issues[key] = issue
        self._dependencies[key] = set()

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._issues.get(self._key(issue_id))

    def update_issue(self, issue_id: str, updates: dict) -> Issue:
        key = self._key(issue_id)
        issue = self._issues[key]
        data = issue.model_dump()
        data.update(updates)
        self._issues[key] = Issue(**data)
        return self._issues[key]

    def close_issue(self, issue_id: str) -> Issue:
        return self.update_issue(issue_id, {"status": IssueStatus.CLOSED})

    def delete_issue(self, issue_id: str) -> None:
        key = self._key(issue_id)
        self._issues.pop(key, None)
        self._dependencies.pop(key, None)
        for deps in self._dependencies.values():
            deps.discard(key)

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
    ) -> list[Issue]:
        result = list(self._issues.values())
        if component_id:
            result = [i for i in result if str(i.component_id) == self._key(component_id)]
        if status:
            result = [i for i in result if i.status == status]
        return result

    # -- Dependency management -----------------------------------------------

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        key = self._key(issue_id)
        dep_key = self._key(depends_on_id)
        self._dependencies.setdefault(key, set()).add(dep_key)

    def remove_dependency(self, issue_id: str, depends_on_id: str) -> None:
        key = self._key(issue_id)
        dep_key = self._key(depends_on_id)
        self._dependencies.get(key, set()).discard(dep_key)

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        key = self._key(issue_id)
        dep_ids = self._dependencies.get(key, set())
        return [self._issues[d] for d in dep_ids if d in self._issues]

    def get_dependents(self, issue_id: str) -> list[Issue]:
        key = self._key(issue_id)
        return [issue for issue in self._issues.values() if key in self._dependencies.get(self._key(issue.id), set())]

    # -- Component CRUD ------------------------------------------------------

    def create_component(self, component: Component) -> None:
        self._components[self._key(component.id)] = component

    def get_component(self, component_id: str) -> Component | None:
        return self._components.get(self._key(component_id))

    def list_components(self, project: str | None = None) -> list[Component]:
        result = list(self._components.values())
        if project:
            result = [c for c in result if c.project == project]
        return result

    def get_blocked_issues(self) -> list[Issue]:
        blocked: list[Issue] = []
        all_issues = list(self._issues.values())
        for issue in all_issues:
            if issue.status == IssueStatus.CLOSED:
                continue
            deps = self.get_dependencies(str(issue.id))
            if any(dep.status != IssueStatus.CLOSED for dep in deps):
                blocked.append(issue)
        return blocked


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture()
def repo() -> FakeRepository:
    return FakeRepository()


@pytest.fixture()
def component(repo: FakeRepository) -> Component:
    comp = Component(name="Backend", project="test-project")
    repo.create_component(comp)
    return comp


@pytest.fixture()
def component2(repo: FakeRepository) -> Component:
    comp = Component(name="Frontend", project="test-project")
    repo.create_component(comp)
    return comp


# -- Tests -------------------------------------------------------------------


class TestCreateIssueAction:
    def test_creates_issue_successfully(self, repo: FakeRepository, component: Component):
        issue = create_issue_action(
            repo,
            title="Fix login",
            component_id=str(component.id),
        )
        assert issue.title == "Fix login"
        assert issue.component_id == component.id
        assert issue.status == IssueStatus.OPEN
        assert repo.get_issue(str(issue.id)) is not None

    def test_raises_when_component_not_found(self, repo: FakeRepository):
        with pytest.raises(ComponentNotFoundError):
            create_issue_action(repo, title="Test", component_id="nonexistent")

    def test_sets_priority(self, repo: FakeRepository, component: Component):
        issue = create_issue_action(
            repo,
            title="Urgent fix",
            component_id=str(component.id),
            priority="CRITICAL",
        )
        assert issue.priority.value == "CRITICAL"

    def test_sets_labels(self, repo: FakeRepository, component: Component):
        issue = create_issue_action(
            repo,
            title="Test",
            component_id=str(component.id),
            labels=["bug", "urgent"],
        )
        assert issue.labels == ["bug", "urgent"]


class TestCloseIssueAction:
    def test_closes_issue(self, repo: FakeRepository, component: Component):
        issue = create_issue_action(repo, title="Test", component_id=str(component.id))
        closed = close_issue_action(repo, str(issue.id))
        assert closed.status == IssueStatus.CLOSED

    def test_raises_when_issue_not_found(self, repo: FakeRepository):
        with pytest.raises(IssueNotFoundError):
            close_issue_action(repo, "nonexistent")

    def test_raises_when_already_closed(self, repo: FakeRepository, component: Component):
        issue = create_issue_action(repo, title="Test", component_id=str(component.id))
        close_issue_action(repo, str(issue.id))
        with pytest.raises(IssueAlreadyClosedError):
            close_issue_action(repo, str(issue.id))

    def test_raises_when_open_dependencies_exist(self, repo: FakeRepository, component: Component):
        dep = create_issue_action(repo, title="Dependency", component_id=str(component.id))
        issue = create_issue_action(repo, title="Main", component_id=str(component.id))
        repo.add_dependency(str(issue.id), str(dep.id))

        with pytest.raises(OpenDependenciesError):
            close_issue_action(repo, str(issue.id))

    def test_closes_when_dependencies_are_closed(self, repo: FakeRepository, component: Component):
        dep = create_issue_action(repo, title="Dependency", component_id=str(component.id))
        issue = create_issue_action(repo, title="Main", component_id=str(component.id))
        repo.add_dependency(str(issue.id), str(dep.id))
        close_issue_action(repo, str(dep.id))

        closed = close_issue_action(repo, str(issue.id))
        assert closed.status == IssueStatus.CLOSED


class TestMoveIssueAction:
    def test_moves_issue_to_new_component(self, repo: FakeRepository, component: Component, component2: Component):
        issue = create_issue_action(repo, title="Test", component_id=str(component.id))
        moved = move_issue_action(repo, str(issue.id), str(component2.id))
        assert moved.component_id == component2.id

    def test_raises_when_issue_not_found(self, repo: FakeRepository, component2: Component):
        with pytest.raises(IssueNotFoundError):
            move_issue_action(repo, "nonexistent", str(component2.id))

    def test_raises_when_target_component_not_found(self, repo: FakeRepository, component: Component):
        issue = create_issue_action(repo, title="Test", component_id=str(component.id))
        with pytest.raises(ComponentNotFoundError):
            move_issue_action(repo, str(issue.id), "nonexistent")


class TestAddDependencyAction:
    def test_adds_dependency(self, repo: FakeRepository, component: Component):
        a = create_issue_action(repo, title="A", component_id=str(component.id))
        b = create_issue_action(repo, title="B", component_id=str(component.id))
        add_dependency_action(repo, str(a.id), str(b.id))

        deps = repo.get_dependencies(str(a.id))
        assert len(deps) == 1
        assert deps[0].id == b.id

    def test_raises_when_issue_not_found(self, repo: FakeRepository, component: Component):
        b = create_issue_action(repo, title="B", component_id=str(component.id))
        with pytest.raises(IssueNotFoundError):
            add_dependency_action(repo, "nonexistent", str(b.id))

    def test_raises_when_target_not_found(self, repo: FakeRepository, component: Component):
        a = create_issue_action(repo, title="A", component_id=str(component.id))
        with pytest.raises(IssueNotFoundError):
            add_dependency_action(repo, str(a.id), "nonexistent")

    def test_raises_on_self_dependency(self, repo: FakeRepository, component: Component):
        a = create_issue_action(repo, title="A", component_id=str(component.id))
        with pytest.raises(CircularDependencyError):
            add_dependency_action(repo, str(a.id), str(a.id))

    def test_raises_on_circular_dependency(self, repo: FakeRepository, component: Component):
        a = create_issue_action(repo, title="A", component_id=str(component.id))
        b = create_issue_action(repo, title="B", component_id=str(component.id))
        c = create_issue_action(repo, title="C", component_id=str(component.id))

        add_dependency_action(repo, str(a.id), str(b.id))
        add_dependency_action(repo, str(b.id), str(c.id))

        # c -> a would create: a -> b -> c -> a (cycle)
        with pytest.raises(CircularDependencyError):
            add_dependency_action(repo, str(c.id), str(a.id))


class TestRemoveDependencyAction:
    def test_removes_dependency(self, repo: FakeRepository, component: Component):
        a = create_issue_action(repo, title="A", component_id=str(component.id))
        b = create_issue_action(repo, title="B", component_id=str(component.id))
        add_dependency_action(repo, str(a.id), str(b.id))
        remove_dependency_action(repo, str(a.id), str(b.id))

        deps = repo.get_dependencies(str(a.id))
        assert len(deps) == 0

    def test_raises_when_issue_not_found(self, repo: FakeRepository, component: Component):
        b = create_issue_action(repo, title="B", component_id=str(component.id))
        with pytest.raises(IssueNotFoundError):
            remove_dependency_action(repo, "nonexistent", str(b.id))


class TestGetBlockedIssuesAction:
    def test_returns_blocked_issues(self, repo: FakeRepository, component: Component):
        dep = create_issue_action(repo, title="Blocker", component_id=str(component.id))
        blocked = create_issue_action(repo, title="Blocked", component_id=str(component.id))
        repo.add_dependency(str(blocked.id), str(dep.id))

        result = get_blocked_issues_action(repo)
        assert len(result) == 1
        assert result[0].id == blocked.id

    def test_excludes_closed_issues(self, repo: FakeRepository, component: Component):
        dep = create_issue_action(repo, title="Blocker", component_id=str(component.id))
        blocked = create_issue_action(repo, title="Blocked", component_id=str(component.id))
        repo.add_dependency(str(blocked.id), str(dep.id))
        close_issue_action(repo, str(dep.id))
        close_issue_action(repo, str(blocked.id))

        result = get_blocked_issues_action(repo)
        assert len(result) == 0

    def test_empty_when_no_blocks(self, repo: FakeRepository, component: Component):
        create_issue_action(repo, title="A", component_id=str(component.id))
        create_issue_action(repo, title="B", component_id=str(component.id))

        result = get_blocked_issues_action(repo)
        assert len(result) == 0


class TestGetDependencyChainAction:
    def test_returns_transitive_chain(self, repo: FakeRepository, component: Component):
        c = create_issue_action(repo, title="C", component_id=str(component.id))
        b = create_issue_action(repo, title="B", component_id=str(component.id))
        a = create_issue_action(repo, title="A", component_id=str(component.id))

        repo.add_dependency(str(a.id), str(b.id))
        repo.add_dependency(str(b.id), str(c.id))

        chain = get_dependency_chain_action(repo, str(a.id))
        chain_ids = {issue.id for issue in chain}
        assert b.id in chain_ids
        assert c.id in chain_ids
        assert len(chain) == 2

    def test_raises_when_issue_not_found(self, repo: FakeRepository):
        with pytest.raises(IssueNotFoundError):
            get_dependency_chain_action(repo, "nonexistent")

    def test_empty_chain_when_no_dependencies(self, repo: FakeRepository, component: Component):
        a = create_issue_action(repo, title="A", component_id=str(component.id))
        chain = get_dependency_chain_action(repo, str(a.id))
        assert len(chain) == 0
