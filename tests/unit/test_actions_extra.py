"""Unit tests for task management actions."""

import pytest
from unittest.mock import MagicMock


class TestActionsModule:
    """Tests for actions module."""

    def test_create_issue_action_exists(self):
        """Test create_issue_action function exists."""
        from socialseed_tasker.core.task_management.actions import create_issue_action
        assert callable(create_issue_action)

    def test_close_issue_action_exists(self):
        """Test close_issue_action function exists."""
        from socialseed_tasker.core.task_management.actions import close_issue_action
        assert callable(close_issue_action)

    def test_move_issue_action_exists(self):
        """Test move_issue_action function exists."""
        from socialseed_tasker.core.task_management.actions import move_issue_action
        assert callable(move_issue_action)

    def test_add_dependency_action_exists(self):
        """Test add_dependency_action function exists."""
        from socialseed_tasker.core.task_management.actions import add_dependency_action
        assert callable(add_dependency_action)

    def test_remove_dependency_action_exists(self):
        """Test remove_dependency_action function exists."""
        from socialseed_tasker.core.task_management.actions import remove_dependency_action
        assert callable(remove_dependency_action)

    def test_get_blocked_issues_action_exists(self):
        """Test get_blocked_issues_action function exists."""
        from socialseed_tasker.core.task_management.actions import get_blocked_issues_action
        assert callable(get_blocked_issues_action)

    def test_get_workable_issues_action_exists(self):
        """Test get_workable_issues_action function exists."""
        from socialseed_tasker.core.task_management.actions import get_workable_issues_action
        assert callable(get_workable_issues_action)

    def test_get_dependency_chain_action_exists(self):
        """Test get_dependency_chain_action function exists."""
        from socialseed_tasker.core.task_management.actions import get_dependency_chain_action
        assert callable(get_dependency_chain_action)

    def test_update_component_action_exists(self):
        """Test update_component_action function exists."""
        from socialseed_tasker.core.task_management.actions import update_component_action
        assert callable(update_component_action)

    def test_delete_component_action_exists(self):
        """Test delete_component_action function exists."""
        from socialseed_tasker.core.task_management.actions import delete_component_action
        assert callable(delete_component_action)

    def test_create_constraint_action_exists(self):
        """Test create_constraint_action function exists."""
        from socialseed_tasker.core.task_management.actions import create_constraint_action
        assert callable(create_constraint_action)

    def test_list_constraints_action_exists(self):
        """Test list_constraints_action function exists."""
        from socialseed_tasker.core.task_management.actions import list_constraints_action
        assert callable(list_constraints_action)

    def test_validate_constraints_action_exists(self):
        """Test validate_constraints_action function exists."""
        from socialseed_tasker.core.task_management.actions import validate_constraints_action
        assert callable(validate_constraints_action)