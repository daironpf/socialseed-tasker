"""Unit tests for terminal CLI utils."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCliCredentialUtils:
    """Tests for CLI credential utilities."""

    def test_load_saved_credentials_returns_dict(self):
        """Test load_saved_credentials returns dict."""
        with patch("socialseed_tasker.cli.utils._CLI_CONFIG_FILE", Path("nonexistent")):
            from socialseed_tasker.cli import utils
            import importlib
            importlib.reload(utils)

            result = utils.load_saved_credentials()
            assert isinstance(result, dict)

    def test_get_config_file_path_returns_path(self):
        """Test get_config_file_path returns Path."""
        with patch("socialseed_tasker.cli.utils._CLI_CONFIG_FILE", Path("test")):
            from socialseed_tasker.cli import utils
            import importlib
            importlib.reload(utils)

            result = utils.get_config_file_path()
            assert isinstance(result, Path)


class TestCliResolver:
    """Tests for CLI resolver utilities."""

    def test_resolver_module_imports(self):
        """Test resolver module can be imported."""
        from socialseed_tasker.cli import resolver

        assert resolver is not None

    def test_resolve_component_id_function_exists(self):
        """Test resolve_component_id function exists."""
        from socialseed_tasker.cli.resolver import resolve_component_id

        assert callable(resolve_component_id)

    def test_resolve_issue_id_function_exists(self):
        """Test resolve_issue_id function exists."""
        from socialseed_tasker.cli.resolver import resolve_issue_id

        assert callable(resolve_issue_id)