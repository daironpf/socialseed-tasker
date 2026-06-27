"""Unit tests for terminal CLI utils module."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCliUtilsModule:
    """Tests for terminal CLI utils module."""

    def test_module_imports(self):
        """Test utils module can be imported."""
        from socialseed_tasker.cli import utils

        assert utils is not None

    def test_load_saved_credentials_function_exists(self):
        """Test load_saved_credentials function exists."""
        from socialseed_tasker.cli.utils import load_saved_credentials

        assert callable(load_saved_credentials)

    def test_save_credentials_function_exists(self):
        """Test save_credentials function exists."""
        from socialseed_tasker.cli.utils import save_credentials

        assert callable(save_credentials)

    def test_clear_credentials_function_exists(self):
        """Test clear_credentials function exists."""
        from socialseed_tasker.cli.utils import clear_credentials

        assert callable(clear_credentials)

    def test_get_config_file_path_function_exists(self):
        """Test get_config_file_path function exists."""
        from socialseed_tasker.cli.utils import get_config_file_path

        assert callable(get_config_file_path)


class TestCliUtilsFunctions:
    """Tests for utility functions."""

    def test_load_saved_returns_dict(self):
        """Test load_saved_credentials returns dict."""
        with patch("socialseed_tasker.cli.utils._CLI_CONFIG_FILE", Path("/nonexistent")):
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


class TestCliUtilsResolver:
    """Tests for resolver module."""

    def test_resolver_module_imports(self):
        """Test resolver module can be imported."""
        from socialseed_tasker.cli import resolver

        assert resolver is not None

    def test_resolve_component_id_function_exists(self):
        """Test resolve_component_id exists."""
        from socialseed_tasker.cli.resolver import resolve_component_id

        assert callable(resolve_component_id)

    def test_resolve_issue_id_function_exists(self):
        """Test resolve_issue_id exists."""
        from socialseed_tasker.cli.resolver import resolve_issue_id

        assert callable(resolve_issue_id)