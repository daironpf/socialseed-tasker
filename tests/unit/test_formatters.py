"""Unit tests for CLI formatters."""

import pytest
from datetime import datetime
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus, IssuePriority


class TestFormatters:
    """Tests for CLI formatters."""

    def test_issues_table_empty(self):
        """Test _issues_table with empty list."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _issues_table

        table = _issues_table([])
        assert table is not None

    def test_issues_table_with_issues(self):
        """Test _issues_table with issue list."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _issues_table
        from uuid import uuid4

        issue = Issue(
            title="Test Issue",
            status=IssueStatus.OPEN,
            priority=IssuePriority.HIGH,
            component_id=uuid4(),
        )
        table = _issues_table([issue])
        assert table is not None

    def test_issues_table_with_component_names(self):
        """Test _issues_table with component names mapping."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _issues_table
        from uuid import uuid4

        issue = Issue(
            title="Test Issue",
            status=IssueStatus.OPEN,
            priority=IssuePriority.HIGH,
            component_id=uuid4(),
        )
        component_names = {str(issue.id): "Backend"}
        table = _issues_table([issue], component_names)
        assert table is not None

    def test_components_table_empty(self):
        """Test _components_table with empty list."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _components_table

        table = _components_table([])
        assert table is not None

    def test_components_table_with_components(self):
        """Test _components_table with component list."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _components_table

        comp = Component(name="Backend", project="test")
        table = _components_table([comp])
        assert table is not None

    def test_dependencies_table_empty(self):
        """Test _dependencies_table with empty lists."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _dependencies_table

        table = _dependencies_table("issue-1", [], [])
        assert table is not None

    def test_dependencies_table_with_depends_on(self):
        """Test _dependencies_table with depends_on list."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _dependencies_table

        deps = [{"id": "dep-1", "title": "Dependency", "status": "OPEN"}]
        table = _dependencies_table("issue-1", deps, [])
        assert table is not None

    def test_dependencies_table_with_blocked_by(self):
        """Test _dependencies_table with blocked_by list."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _dependencies_table

        blocked = [{"id": "block-1", "title": "Blocked", "status": "OPEN"}]
        table = _dependencies_table("issue-1", [], blocked)
        assert table is not None

    def test_dependency_tree_empty(self):
        """Test _dependency_tree with empty deps."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _dependency_tree

        tree = _dependency_tree("issue-1", [], "Dependencies")
        assert tree is not None

    def test_dependency_tree_with_deps(self):
        """Test _dependency_tree with deps list."""
        from socialseed_tasker.entrypoints.terminal_cli.formatters import _dependency_tree

        deps = [{"id": "dep-1", "title": "Some dependency"}]
        tree = _dependency_tree("issue-1", deps, "Dependencies")
        assert tree is not None