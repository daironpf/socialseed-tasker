"""Tests for container and configuration."""

import os
import tempfile
from pathlib import Path

import pytest

from socialseed_tasker.bootstrap.container import (
    AppConfig,
    StorageConfig,
    Neo4jConfig,
    Neo4jConnectionMode,
    Container,
)


class TestNeo4jConfig:
    def test_default_values(self):
        config = Neo4jConfig()
        assert config.uri == "bolt://localhost:7687"
        assert config.user == "neo4j"
        assert config.password == ""
        assert config.database == "neo4j"

    def test_from_uri_local(self):
        config = Neo4jConfig.from_uri("bolt://localhost:7687")
        assert config.uri == "bolt://localhost:7687"
        assert config.connection_mode == Neo4jConnectionMode.LOCAL

    def test_from_uri_aura(self):
        config = Neo4jConfig.from_uri("neo4j+s://my-aura-db.databases.neo4j.io")
        assert config.connection_mode == Neo4jConnectionMode.AURA


class TestStorageConfig:
    def test_default_values(self):
        config = StorageConfig()
        assert config.backend == "file"
        assert config.file_path == Path(".tasker-data")

    def test_neo4j_config(self):
        config = StorageConfig(backend="neo4j", neo4j=Neo4jConfig(uri="bolt://test"))
        assert config.backend == "neo4j"
        assert config.neo4j.uri == "bolt://test"


class TestAppConfig:
    def test_default_values(self):
        config = AppConfig()
        assert config.storage.backend == "file"
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.debug is False

    def test_from_env_default(self, monkeypatch):
        monkeypatch.delenv("TASKER_NEO4J_URI", raising=False)
        monkeypatch.delenv("TASKER_STORAGE_BACKEND", raising=False)
        config = AppConfig.from_env()
        assert config.storage.backend == "file"

    def test_from_env_neo4j(self, monkeypatch):
        monkeypatch.setenv("TASKER_STORAGE_BACKEND", "neo4j")
        monkeypatch.setenv("TASKER_NEO4J_URI", "bolt://custom:7687")
        config = AppConfig.from_env()
        assert config.storage.backend == "neo4j"
        assert config.storage.neo4j.uri == "bolt://custom:7687"

    def test_from_env_invalid_backend(self, monkeypatch):
        monkeypatch.setenv("TASKER_STORAGE_BACKEND", "invalid")
        with pytest.raises(ValueError, match="Invalid storage backend"):
            AppConfig.from_env()


class TestContainer:
    def test_from_env_creates_container(self):
        container = Container.from_env()
        assert container.config.storage.backend == "file"

    def test_get_repository_file_backend(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TASKER_STORAGE_BACKEND", "file")
        monkeypatch.setenv("TASKER_FILE_PATH", str(tmp_path))
        container = Container.from_env()
        repo = container.get_repository()
        assert repo is not None

    def test_initialize_no_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TASKER_STORAGE_BACKEND", "file")
        monkeypatch.setenv("TASKER_FILE_PATH", str(tmp_path))
        container = Container.from_env()
        container.initialize()
