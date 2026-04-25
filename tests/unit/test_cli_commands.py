"""Tests for CLI commands using Typer CliRunner with in-memory mock repository."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.constraints import Constraint, ConstraintLevel, ConstraintCategory
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus, IssuePriority
from socialseed_tasker.entrypoints.terminal_cli.app import app


class MockRepository(TaskRepositoryInterface):
    """In-memory mock repository for CLI testing."""

    def __init__(self) -> None:
        self._issues: dict[str, Issue] = {}
        self._components: dict[str, Component] = {}
        self._dependencies: dict[str, set[str]] = {}
        self._constraints: dict[str, Constraint] = {}

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
        status: IssueStatus | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        issues = list(self._issues.values())
        if component_id:
            issues = [i for i in issues if str(i.component_id) == component_id]
        if status:
            issues = [i for i in issues if i.status == status]
        if project:
            issues = [
                i
                for i in issues
                if self._components.get(str(i.component_id), Component(name="", project="")).project == project
            ]
        return issues

    def get_workable_issues(
        self,
        priority: str | None = None,
        component_id: str | None = None,
    ) -> list[Issue]:
        issues = []
        for issue in self._issues.values():
            if issue.status == IssueStatus.CLOSED:
                continue
            if priority and issue.priority.value != priority:
                continue
            if component_id and str(issue.component_id) != component_id:
                continue
            deps = self._dependencies.get(str(issue.id), set())
            all_closed = all(
                self._issues.get(d) and self._issues[d].status == IssueStatus.CLOSED
                for d in deps if d in self._issues
            )
            if not all_closed:
                continue
            issues.append(issue)
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
        count = {"issues": len(self._issues), "components": len(self._components)}
        self._issues.clear()
        self._components.clear()
        self._dependencies.clear()
        self._constraints.clear()
        return count

    @contextmanager
    def transaction(self) -> Iterator[None]:
        yield


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_repo():
    return MockRepository()


def _patch_commands(mock_repo: MockRepository):
    """Patch commands.get_repository to return mock_repo."""
    from socialseed_tasker.entrypoints.terminal_cli import commands as cmds
    from socialseed_tasker.entrypoints.terminal_cli import app as cli_app

    original = cmds.get_repository
    cmds.get_repository = lambda: mock_repo
    cli_app._cli_container = None
    return original


def _unpatch_commands(original):
    """Restore original get_repository."""
    from socialseed_tasker.entrypoints.terminal_cli import commands as cmds

    cmds.get_repository = original


class TestIssueCommands:
    def test_issue_create_success(self, runner, mock_repo):
        comp = Component(name="TestComp", project="test")
        mock_repo.create_component(comp)
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["issue", "create", "Test Issue", "-c", str(comp.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_issue_list_empty(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["issue", "list"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_issue_create_missing_component(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["issue", "create", "Test", "-c", "nonexistent"])
            assert result.exit_code == 2
        finally:
            _unpatch_commands(original)

    def test_issue_show_missing(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["issue", "show", "nonexistent-id"])
            assert result.exit_code == 1
        finally:
            _unpatch_commands(original)


class TestComponentCommands:
    def test_component_create_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["component", "create", "Backend", "-p", "project1"])
            assert result.exit_code == 0
            assert "created" in result.stdout.lower()
        finally:
            _unpatch_commands(original)

    def test_component_list_empty(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["component", "list"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_component_list_with_data(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            runner.invoke(app, ["component", "create", "Frontend", "-p", "project1"])
            result = runner.invoke(app, ["component", "list"])
            assert result.exit_code == 0
            assert "Frontend" in result.stdout
        finally:
            _unpatch_commands(original)

    def test_component_show_missing(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["component", "show", "nonexistent-id"])
            assert result.exit_code == 2
        finally:
            _unpatch_commands(original)

    def test_component_update_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            create_result = runner.invoke(app, ["component", "create", "OldName", "-p", "proj"])
            assert create_result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_component_delete_missing(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["component", "delete", "nonexistent-id"])
            assert result.exit_code == 1
        finally:
            _unpatch_commands(original)


class TestDependencyCommands:
    def test_dependency_blocked_empty(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["dependency", "blocked"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestStatusCommand:
    def test_status_command(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "Backend" in result.stdout
            assert "neo4j" in result.stdout.lower()
        finally:
            _unpatch_commands(original)


class TestGlobalOptions:
    def test_help_option(self, runner):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "neo4j-uri" in result.stdout.lower()


class TestComponentListJson:
    def test_component_list_json(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            runner.invoke(app, ["component", "create", "TestComp", "-p", "proj"])
            result = runner.invoke(app, ["component", "list", "--json"])
            assert result.exit_code == 0
            assert "[" in result.stdout
        finally:
            _unpatch_commands(original)


class TestInitCommand:
    def test_init_creates_scaffold_files(self, runner, tmp_path):
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        result = runner.invoke(
            app,
            ["init", str(target_dir)],
        )
        assert result.exit_code == 0
        assert (target_dir / "tasker").exists()
        assert (target_dir / "tasker" / "docker-compose.yml").exists()

    def test_init_force_overwrites_existing(self, runner, tmp_path):
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        tasker_dir = target_dir / "tasker"
        tasker_dir.mkdir()
        (tasker_dir / "docker-compose.yml").write_text("old content")

        result = runner.invoke(
            app,
            ["init", str(target_dir), "--force"],
        )
        assert result.exit_code == 0
        assert "Overwritten" in result.stdout

    def test_init_nonexistent_directory(self, runner, tmp_path):
        target_dir = tmp_path / "nonexistent"
        result = runner.invoke(
            app,
            ["init", str(target_dir)],
        )
        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_init_short_flag_force(self, runner, tmp_path):
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        tasker_dir = target_dir / "tasker"
        tasker_dir.mkdir()

        result = runner.invoke(
            app,
            ["init", str(target_dir), "-f"],
        )
        assert result.exit_code == 0


class TestIssueListCommand:
    def test_issue_list_with_issues(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "list"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_issue_list_filter_by_status(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "list", "--status", "OPEN"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_issue_list_json(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "list", "--json"])
            assert result.exit_code == 0
            assert "[" in result.stdout or "{" in result.stdout
        finally:
            _unpatch_commands(original)

    def test_issue_list_filter_by_project(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="testproject")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["issue", "list", "--project", "testproject"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestIssueShowCommand:
    def test_issue_show_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue_id = uuid4()
            issue = Issue(
                id=issue_id,
                title="Show Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.MEDIUM,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "show", str(issue_id)])
            assert result.exit_code == 0
            assert "Show Test Issue" in result.stdout
        finally:
            _unpatch_commands(original)

    def test_issue_show_by_prefix(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue_id = uuid4()
            issue = Issue(
                id=issue_id,
                title="Prefix Search Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.LOW,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "show", str(issue_id)[:8]])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestIssueCloseCommand:
    def test_issue_close_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Close Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "close", str(issue.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_issue_close_nonexistent(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["issue", "close", "nonexistent-id"])
            assert result.exit_code == 1
        finally:
            _unpatch_commands(original)


class TestIssueMoveCommand:
    def test_issue_move_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp1 = Component(name="Comp1", project="test")
            comp2 = Component(name="Comp2", project="test")
            mock_repo.create_component(comp1)
            mock_repo.create_component(comp2)
            issue = Issue(
                id=uuid4(),
                title="Move Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.MEDIUM,
                component_id=comp1.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "move", str(issue.id), str(comp2.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestIssueDeleteCommand:
    def test_issue_delete_with_confirmation(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Delete Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.LOW,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "delete", str(issue.id), "--force"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestIssueStartFinishCommand:
    def test_issue_start_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Start Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "start", str(issue.id), "--agent-id", "test-agent"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_issue_finish_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Finish Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "finish", str(issue.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestComponentShowCommand:
    def test_component_show_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="ShowComp", project="test", description="Test description")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "show", comp.name])
            assert result.exit_code == 0
            assert "ShowComp" in result.stdout
        finally:
            _unpatch_commands(original)

    def test_component_show_by_id(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="ShowByIdComp", project="test")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "show", str(comp.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestComponentUpdateCommand:
    def test_component_update_name(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="OldComp", project="test")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "update", comp.name, "--name", "NewComp"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_component_update_description(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="UpdateComp", project="test")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "update", comp.name, "--description", "New desc"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_component_update_no_fields(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="NoFieldsComp", project="test")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "update", comp.name])
            assert result.exit_code == 1
        finally:
            _unpatch_commands(original)


class TestComponentDeleteCommand:
    def test_component_delete_invokes(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="DeleteComp", project="test")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "delete", str(comp.id), "--yes"])
        finally:
            _unpatch_commands(original)


class TestComponentListCommand:
    def test_component_list_by_project(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            Component(name="Proj1Comp1", project="proj1")
            Component(name="Proj1Comp2", project="proj1")
            mock_repo.create_component(Component(name="Proj1Comp1", project="proj1"))
            mock_repo.create_component(Component(name="Proj1Comp2", project="proj1"))
            result = runner.invoke(app, ["component", "list", "--project", "proj1"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)

    def test_component_list_all(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            mock_repo.create_component(Component(name="Comp1", project="proj1"))
            mock_repo.create_component(Component(name="Comp2", project="proj2"))
            result = runner.invoke(app, ["component", "list", "--all"])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestDependencyAddCommand:
    def test_dependency_add_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue1 = Issue(
                id=uuid4(),
                title="Issue 1",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            issue2 = Issue(
                id=uuid4(),
                title="Issue 2",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue1)
            mock_repo.create_issue(issue2)
            result = runner.invoke(app, ["dependency", "add", str(issue1.id), str(issue2.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestDependencyListCommand:
    def test_dependency_list_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="List Dep Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.MEDIUM,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["dependency", "list", str(issue.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestDependencyChainCommand:
    def test_dependency_chain_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Chain Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["dependency", "chain", str(issue.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestAnalyzeCommand:
    def test_analyze_impact_success(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Impact Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.CRITICAL,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["analyze", "impact", str(issue.id)])
            assert result.exit_code == 0
        finally:
            _unpatch_commands(original)


class TestConstraintsCommands:
    def test_constraints_list_invokes(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["constraints", "list"])
        finally:
            _unpatch_commands(original)


class TestSeedCommand:
    def test_seed_run_invokes(self, runner, mock_repo):
        original = _patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["seed", "run"])
        finally:
            _unpatch_commands(original)


class TestProjectDetectCommand:
    def test_project_detect_invokes(self, runner, tmp_path):
        project_dir = tmp_path / "testproject"
        project_dir.mkdir()
        result = runner.invoke(app, ["project", "detect", "--path", str(project_dir)])

    def test_project_detect_with_short_flag(self, runner, tmp_path):
        project_dir = tmp_path / "testproject2"
        project_dir.mkdir()
        result = runner.invoke(app, ["project", "detect", "-p", str(project_dir)])
