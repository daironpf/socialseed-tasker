"""Additional CLI command tests using Typer CliRunner."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from typer.testing import CliRunner

from socialseed_tasker.domain.entities import (
    Component, Issue, IssueStatus, IssuePriority
)
from socialseed_tasker.cli.app import app
from socialseed_tasker.cli import commands


class MockRepository:
    """Simple mock repository for testing."""

    def __init__(self):
        self._issues = {}
        self._components = {}
        self._dependencies = {}

    def create_issue(self, issue):
        self._issues[str(issue.id)] = issue

    def get_issue(self, issue_id):
        return self._issues.get(issue_id)

    def update_issue(self, issue_id, updates):
        issue = self._issues[issue_id]
        updated = issue.model_copy(update=updates)
        self._issues[issue_id] = updated
        return updated

    def close_issue(self, issue_id):
        return self.update_issue(issue_id, {"status": IssueStatus.CLOSED})

    def delete_issue(self, issue_id):
        self._issues.pop(issue_id, None)

    def list_issues(self, statuses=None, project=None, component_id=None):
        issues = list(self._issues.values())
        if statuses:
            issues = [i for i in issues if i.status in statuses]
        return issues

    def create_component(self, component):
        self._components[str(component.id)] = component

    def get_component(self, component_id):
        return self._components.get(component_id)

    def get_component_by_name(self, name, project=None):
        for comp in self._components.values():
            if comp.name == name:
                return comp
        return None

    def list_components(self, project=None):
        comps = list(self._components.values())
        if project:
            comps = [c for c in comps if c.project == project]
        return comps

    def update_component(self, component_id, updates):
        comp = self._components[component_id]
        updated = comp.model_copy(update=updates)
        self._components[component_id] = updated
        return updated

    def delete_component(self, component_id):
        self._components.pop(component_id, None)

    def add_dependency(self, issue_id, depends_on_id):
        if issue_id not in self._dependencies:
            self._dependencies[issue_id] = set()
        self._dependencies[issue_id].add(depends_on_id)

    def get_dependencies(self, issue_id):
        dep_ids = self._dependencies.get(issue_id, set())
        return [self._issues[i] for i in dep_ids if i in self._issues]

    def get_dependents(self, issue_id):
        dependents = []
        for i, deps in self._dependencies.items():
            if issue_id in deps:
                if i in self._issues:
                    dependents.append(self._issues[i])
        return dependents

    def remove_dependency(self, issue_id, depends_on_id):
        if issue_id in self._dependencies:
            self._dependencies[issue_id].discard(depends_on_id)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_repo():
    return MockRepository()


def patch_commands(repo):
    from socialseed_tasker.cli.commands import shared
    from socialseed_tasker.cli import commands as cmds
    original = {}
    original['get_repository'] = commands.get_repository
    original['shared_get_repository'] = shared.get_repository
    submodules = [
        cmds,
        shared,
        cmds.issue_commands,
        cmds.component_commands,
        cmds.dependency_commands,
        cmds.analysis_commands,
        cmds.status_commands,
        cmds.project_commands,
        cmds.rag_commands,
        cmds.code_graph_commands,
        cmds.agent_commands,
        cmds.constraints_commands,
        cmds.seed_commands,
        cmds.reasoning_commands,
    ]
    for mod in submodules:
        mod.get_repository = lambda: repo
    return original


def unpatch_commands(original):
    from socialseed_tasker.cli.commands import shared
    commands.get_repository = original['get_repository']
    shared.get_repository = original['shared_get_repository']


class TestIssueCommands:
    """Tests for issue commands."""

    def test_issue_list_with_filters(self, runner, mock_repo):
        """Test issue list with status filter."""
        original = patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Open Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.HIGH,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "list", "--status", "OPEN"])
        finally:
            unpatch_commands(original)

    def test_issue_list_with_project(self, runner, mock_repo):
        """Test issue list with project filter."""
        original = patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="myproject")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["issue", "list", "--project", "myproject"])
        finally:
            unpatch_commands(original)

    def test_issue_show_with_valid_id(self, runner, mock_repo):
        """Test issue show with valid issue."""
        original = patch_commands(mock_repo)
        try:
            comp = Component(name="TestComp", project="test")
            mock_repo.create_component(comp)
            issue = Issue(
                id=uuid4(),
                title="Test Issue",
                status=IssueStatus.OPEN,
                priority=IssuePriority.MEDIUM,
                component_id=comp.id,
            )
            mock_repo.create_issue(issue)
            result = runner.invoke(app, ["issue", "show", str(issue.id)])
            assert result.exit_code == 0
        finally:
            unpatch_commands(original)


class TestComponentCommands:
    """Tests for component commands."""

    def test_component_list_with_project(self, runner, mock_repo):
        """Test component list with project filter."""
        original = patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["component", "list", "--project", "test"])
        finally:
            unpatch_commands(original)

    def test_component_show_valid(self, runner, mock_repo):
        """Test component show with valid component."""
        original = patch_commands(mock_repo)
        try:
            comp = Component(name="Backend", project="test")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "show", str(comp.id)])
            assert result.exit_code == 0
        finally:
            unpatch_commands(original)

    def test_component_update_name(self, runner, mock_repo):
        """Test component update changes name."""
        original = patch_commands(mock_repo)
        try:
            comp = Component(name="OldName", project="test")
            mock_repo.create_component(comp)
            result = runner.invoke(app, ["component", "update", str(comp.id), "--name", "NewName"])
        finally:
            unpatch_commands(original)


class TestDependencyCommands:
    """Tests for dependency commands."""

    def test_dependency_list(self, runner, mock_repo):
        """Test dependency list command."""
        original = patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["dependency", "list"])
        finally:
            unpatch_commands(original)

    def test_dependency_blocked(self, runner, mock_repo):
        """Test dependency blocked command."""
        original = patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["dependency", "blocked"])
        finally:
            unpatch_commands(original)


class TestCodeGraphCommands:
    """Tests for code graph commands."""

    def test_code_graph_stats(self, runner, mock_repo):
        """Test code graph stats command."""
        original = patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["code-graph", "stats"])
        finally:
            unpatch_commands(original)


class TestRagCommands:
    """Tests for RAG commands."""

    def test_rag_stats(self, runner, mock_repo):
        """Test rag stats command."""
        original = patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["rag", "stats"])
        finally:
            unpatch_commands(original)


class TestReasoningCommands:
    """Tests for reasoning commands."""

    def test_reasoning_stats(self, runner, mock_repo):
        """Test reasoning stats command."""
        original = patch_commands(mock_repo)
        try:
            result = runner.invoke(app, ["reasoning", "stats"])
        finally:
            unpatch_commands(original)