"""Unit tests for web API main module."""

import pytest
from unittest.mock import patch, MagicMock


class TestWebApiMain:
    """Tests for web_api __main__ module."""

    def test_main_function_exists(self):
        """Test main function exists."""
        from socialseed_tasker.entrypoints.web_api import __main__

        assert hasattr(__main__, "main")
        assert callable(__main__.main)

    def test_seed_demo_data_function_exists(self):
        """Test _seed_demo_data function exists."""
        from socialseed_tasker.entrypoints.web_api import __main__

        assert hasattr(__main__, "_seed_demo_data")
        assert callable(__main__._seed_demo_data)

    @patch("socialseed_tasker.entrypoints.web_api.__main__.Container")
    @patch("socialseed_tasker.entrypoints.web_api.__main__.create_app")
    @patch("socialseed_tasker.entrypoints.web_api.__main__.uvicorn")
    def test_main_creates_app(self, mock_uvicorn, mock_create_app, mock_container):
        """Test main creates FastAPI app."""
        from socialseed_tasker.entrypoints.web_api.__main__ import main

        mock_container_instance = MagicMock()
        mock_container.from_env.return_value = mock_container_instance
        mock_container_instance.get_repository.return_value = MagicMock()
        mock_container_instance.get_driver.return_value = MagicMock()
        mock_container_instance.config.api_host = "0.0.0.0"
        mock_container_instance.config.api_port = 8000
        mock_container_instance.config.debug = False

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        mock_server = MagicMock()
        mock_uvicorn.Config.return_value = MagicMock()
        mock_uvicorn.Server.return_value = mock_server

        main()

        mock_create_app.assert_called_once()

    def test_seed_demo_data_returns_when_components_exist(self):
        """Test _seed_demo_data returns early when demo data exists."""
        from socialseed_tasker.entrypoints.web_api.__main__ import _seed_demo_data

        mock_repo = MagicMock()
        mock_repo.list_components.return_value = ["existing"]

        _seed_demo_data(mock_repo)

        mock_repo.create_component.assert_not_called()





class TestBootstrapWiring:
    """Tests for bootstrap wiring module."""

    def test_wire_api_function_exists(self):
        """Test wire_api function exists."""
        from socialseed_tasker.bootstrap.wiring import wire_api

        assert callable(wire_api)

    def test_wire_cli_function_exists(self):
        """Test wire_cli function exists."""
        from socialseed_tasker.bootstrap.wiring import wire_cli

        assert callable(wire_cli)

    def test_get_driver_function_exists(self):
        """Test get_driver function exists."""
        from socialseed_tasker.bootstrap.wiring import get_driver

        assert callable(get_driver)