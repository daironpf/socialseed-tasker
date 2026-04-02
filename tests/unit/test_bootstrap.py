"""Tests for the bootstrap container and configuration."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from socialseed_tasker.bootstrap.container import AppConfig, Container, Neo4jConfig, StorageConfig


class TestAppConfig:
    def test_default_config(self):
        config = AppConfig()
        assert config.storage.backend == "file"
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.debug is False

    def test_from_env_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            config = AppConfig.from_env()
            assert config.storage.backend == "file"
            assert config.storage.neo4j.uri == "bolt://localhost:7687"

    def test_from_env_overrides(self):
        env = {
            "TASKER_STORAGE_BACKEND": "neo4j",
            "TASKER_NEO4J_URI": "bolt://custom:9999",
            "TASKER_NEO4J_USER": "admin",
            "TASKER_NEO4J_PASSWORD": "secret",
            "TASKER_FILE_PATH": "/custom/path",
            "TASKER_API_HOST": "127.0.0.1",
            "TASKER_API_PORT": "9000",
            "TASKER_DEBUG": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            config = AppConfig.from_env()
            assert config.storage.backend == "neo4j"
            assert config.storage.neo4j.uri == "bolt://custom:9999"
            assert config.storage.neo4j.user == "admin"
            assert config.storage.neo4j.password == "secret"
            assert config.api_host == "127.0.0.1"
            assert config.api_port == 9000
            assert config.debug is True

    def test_invalid_backend_raises(self):
        with patch.dict(os.environ, {"TASKER_STORAGE_BACKEND": "invalid"}, clear=True):
            with pytest.raises(ValueError, match="Invalid storage backend"):
                AppConfig.from_env()


class TestContainer:
    def test_from_env(self):
        with patch.dict(os.environ, {}, clear=True):
            container = Container.from_env()
            assert container.config.storage.backend == "file"

    def test_get_repository_file_backend(self, tmp_path):
        config = AppConfig(
            storage=StorageConfig(backend="file", file_path=tmp_path),
        )
        container = Container(config=config)
        repo = container.get_repository()
        assert repo is not None

    def test_cleanup(self, tmp_path):
        config = AppConfig(
            storage=StorageConfig(backend="file", file_path=tmp_path),
        )
        container = Container(config=config)
        container.get_repository()
        container.cleanup()
        assert container._repository is None

    def test_health_check_file_backend(self, tmp_path):
        config = AppConfig(
            storage=StorageConfig(backend="file", file_path=tmp_path),
        )
        container = Container(config=config)
        assert container.health_check() is True

    def test_health_check_missing_path(self):
        config = AppConfig(
            storage=StorageConfig(backend="file", file_path=Path("/nonexistent/path")),
        )
        container = Container(config=config)
        assert container.health_check() is False

    def test_initialize(self, tmp_path):
        config = AppConfig(
            storage=StorageConfig(backend="file", file_path=tmp_path),
        )
        container = Container(config=config)
        container.initialize()
        assert container._repository is not None
