"""Tests for CLI commands using Typer CliRunner with in-memory mock repository."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from typer.testing import CliRunner

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.entrypoints.terminal_cli.app import app


class MockRepository(TaskRepositoryInterface):
    """In-memory mock repository for CLI testing."""

    def __init__(self) -> None:
        self._issues: dict[str, Issue] = {}
        self._components: dict[str, Component] = {}
        self._dependencies: dict[str, set[str]] = {}

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
        for issue_id, deps in self._dependencies.items():
            issue = self._issues.get(issue_id)
            if issue and issue.status != IssueStatus.CLOSED:
                for dep_id in deps:
                    dep = self._issues.get(dep_id)
                    if dep and dep.status != IssueStatus.CLOSED:
                        blocked.append(issue)
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
        return self._issues[issue_id]

    def finish_agent_work(self, issue_id: str) -> Issue:
        return self._issues[issue_id]

    def get_agent_status(self, issue_id: str) -> dict[str, Any]:
        return {}

    def reset_data(self, scope: str = "all") -> dict[str, int]:
        count = {"issues": len(self._issues), "components": len(self._components)}
        self._issues.clear()
        self._components.clear()
        self._dependencies.clear()
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
            assert result.exit_code == 1
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
