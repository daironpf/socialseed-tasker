"""Tests for the bootstrap container and configuration."""

import os
from unittest.mock import patch

import pytest

from socialseed_tasker.bootstrap.container import AppConfig, Container, Neo4jConfig, Neo4jConnectionMode


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


class TestAppConfig:
    def test_default_config(self):
        config = AppConfig()
        assert config.neo4j.uri == "bolt://localhost:7687"
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.debug is False

    def test_from_env_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            config = AppConfig.from_env()
            assert config.neo4j.uri == "bolt://localhost:7687"
            assert config.api_host == "0.0.0.0"
            assert config.api_port == 8000

    def test_from_env_overrides(self):
        env = {
            "TASKER_NEO4J_URI": "bolt://custom:9999",
            "TASKER_NEO4J_USER": "admin",
            "TASKER_NEO4J_PASSWORD": "secret",
            "TASKER_API_HOST": "127.0.0.1",
            "TASKER_API_PORT": "9000",
            "TASKER_DEBUG": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            config = AppConfig.from_env()
            assert config.neo4j.uri == "bolt://custom:9999"
            assert config.neo4j.user == "admin"
            assert config.neo4j.password == "secret"
            assert config.api_host == "127.0.0.1"
            assert config.api_port == 9000
            assert config.debug is True


class TestContainer:
    def test_from_env(self):
        with patch.dict(os.environ, {}, clear=True):
            container = Container.from_env()
            assert container.config.neo4j.uri == "bolt://localhost:7687"

    def test_container_default_config(self):
        container = Container()
        assert container.config.neo4j.uri == "bolt://localhost:7687"

    def test_container_custom_config(self):
        neo4j_cfg = Neo4jConfig(uri="bolt://custom:7687", user="admin", password="secret")
        config = AppConfig(neo4j=neo4j_cfg)
        container = Container(config=config)
        assert container.config.neo4j.uri == "bolt://custom:7687"
