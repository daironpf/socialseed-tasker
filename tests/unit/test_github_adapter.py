"""Unit tests for GitHub adapter module."""

import pytest


class TestGitHubAdapter:
    """Tests for GitHub adapter module."""

    def test_github_adapter_class_exists(self):
        """Test GitHubAdapter class exists."""
        from socialseed_tasker.storage.adapters.github import GitHubAdapter

        assert GitHubAdapter is not None

    def test_github_issue_model_exists(self):
        """Test GitHubIssue model exists."""
        from socialseed_tasker.storage.adapters.github import GitHubIssue

        assert GitHubIssue is not None

    def test_github_milestone_model_exists(self):
        """Test GitHubMilestone model exists."""
        from socialseed_tasker.storage.adapters.github import GitHubMilestone

        assert GitHubMilestone is not None