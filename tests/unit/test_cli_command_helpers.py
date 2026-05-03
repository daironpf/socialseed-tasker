"""Unit tests for CLI command helpers."""

import pytest
from unittest.mock import MagicMock, patch
from socialseed_tasker.core.task_management.entities import IssueStatus, IssuePriority


class TestCliCommandHelpers:
    """Tests for CLI command helper functions."""

    def test_status_style_returns_string(self):
        """Test _status_style returns a styled string."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import _status_style

        result = _status_style(IssueStatus.OPEN)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_status_style_closed(self):
        """Test _status_style for CLOSED status."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import _status_style

        result = _status_style(IssueStatus.CLOSED)
        assert isinstance(result, str)

    def test_priority_style_returns_string(self):
        """Test _priority_style returns a styled string."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import _priority_style

        result = _priority_style(IssuePriority.HIGH)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_priority_style_low(self):
        """Test _priority_style for LOW priority."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import _priority_style

        result = _priority_style(IssuePriority.LOW)
        assert isinstance(result, str)

    def test_priority_style_medium(self):
        """Test _priority_style for MEDIUM priority."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import _priority_style

        result = _priority_style(IssuePriority.MEDIUM)
        assert isinstance(result, str)

    def test_priority_style_critical(self):
        """Test _priority_style for CRITICAL priority."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import _priority_style

        result = _priority_style(IssuePriority.CRITICAL)
        assert isinstance(result, str)





class TestStatusCommand:
    """Tests for status command."""

    def test_status_command_exists(self):
        """Test status_command function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import status_command

        assert callable(status_command)


class TestProjectCommands:
    """Tests for project commands."""

    def test_project_detect_exists(self):
        """Test project_detect function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import project_detect

        assert callable(project_detect)

    def test_project_setup_exists(self):
        """Test project_setup function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import project_setup

        assert callable(project_setup)


class TestSeedRun:
    """Tests for seed run command."""

    def test_seed_run_exists(self):
        """Test seed_run function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import seed_run

        assert callable(seed_run)


class TestCodeGraphCommands:
    """Tests for code graph commands."""

    def test_code_graph_scan_exists(self):
        """Test code_graph_scan function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_scan

        assert callable(code_graph_scan)

    def test_code_graph_find_exists(self):
        """Test code_graph_find function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_find

        assert callable(code_graph_find)

    def test_code_graph_files_exists(self):
        """Test code_graph_files function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_files

        assert callable(code_graph_files)

    def test_code_graph_stats_exists(self):
        """Test code_graph_stats function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_stats

        assert callable(code_graph_stats)

    def test_code_graph_clear_exists(self):
        """Test code_graph_clear function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_clear

        assert callable(code_graph_clear)

    def test_code_graph_impact_exists(self):
        """Test code_graph_impact function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_impact

        assert callable(code_graph_impact)

    def test_code_graph_calls_exists(self):
        """Test code_graph_calls function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_calls

        assert callable(code_graph_calls)

    def test_code_graph_depends_exists(self):
        """Test code_graph_depends function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_depends

        assert callable(code_graph_depends)

    def test_code_graph_tests_exists(self):
        """Test code_graph_tests function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import code_graph_tests

        assert callable(code_graph_tests)


class TestRagCommands:
    """Tests for RAG commands."""

    def test_rag_search_exists(self):
        """Test rag_search function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import rag_search

        assert callable(rag_search)

    def test_rag_index_exists(self):
        """Test rag_index function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import rag_index

        assert callable(rag_index)

    def test_rag_stats_exists(self):
        """Test rag_stats function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import rag_stats

        assert callable(rag_stats)

    def test_rag_clear_exists(self):
        """Test rag_clear function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import rag_clear

        assert callable(rag_clear)


class TestReasoningCommands:
    """Tests for reasoning commands."""

    def test_reasoning_log_exists(self):
        """Test reasoning_log function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import reasoning_log

        assert callable(reasoning_log)

    def test_reasoning_history_exists(self):
        """Test reasoning_history function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import reasoning_history

        assert callable(reasoning_history)

    def test_reasoning_stats_exists(self):
        """Test reasoning_stats function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import reasoning_stats

        assert callable(reasoning_stats)

    def test_reasoning_clear_exists(self):
        """Test reasoning_clear function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import reasoning_clear

        assert callable(reasoning_clear)


class TestAgentCommands:
    """Tests for agent commands."""

    def test_agent_context_exists(self):
        """Test agent_context function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import agent_context

        assert callable(agent_context)

    def test_agent_suggest_exists(self):
        """Test agent_suggest function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import agent_suggest

        assert callable(agent_suggest)

    def test_agent_reasoning_exists(self):
        """Test agent_reasoning function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import agent_reasoning

        assert callable(agent_reasoning)


class TestConstraintsCommands:
    """Tests for constraints commands."""

    def test_constraints_set_exists(self):
        """Test constraints_set function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import constraints_set

        assert callable(constraints_set)

    def test_constraints_list_exists(self):
        """Test constraints_list function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import constraints_list

        assert callable(constraints_list)

    def test_constraints_validate_exists(self):
        """Test constraints_validate function exists."""
        from socialseed_tasker.entrypoints.terminal_cli.commands import constraints_validate

        assert callable(constraints_validate)