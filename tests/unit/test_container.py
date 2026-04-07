"""Tests for container and configuration."""

from socialseed_tasker.bootstrap.container import (
    AppConfig,
    Container,
    Neo4jConfig,
    Neo4jConnectionMode,
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

    def test_from_uri_bolt_plus(self):
        config = Neo4jConfig.from_uri("bolt+s://my-db.databases.neo4j.io")
        assert config.connection_mode == Neo4jConnectionMode.AURA


class TestAppConfig:
    def test_default_values(self):
        config = AppConfig()
        assert config.neo4j.uri == "bolt://localhost:7687"
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8000
        assert config.debug is False

    def test_from_env_default(self, monkeypatch):
        monkeypatch.delenv("TASKER_NEO4J_URI", raising=False)
        config = AppConfig.from_env()
        assert config.neo4j.uri == "bolt://localhost:7687"

    def test_from_env_neo4j(self, monkeypatch):
        monkeypatch.setenv("TASKER_NEO4J_URI", "bolt://custom:7687")
        config = AppConfig.from_env()
        assert config.neo4j.uri == "bolt://custom:7687"

    def test_custom_config(self):
        neo4j_cfg = Neo4jConfig(uri="bolt://test:9999", user="admin")
        config = AppConfig(neo4j=neo4j_cfg, api_host="127.0.0.1", api_port=9000)
        assert config.neo4j.uri == "bolt://test:9999"
        assert config.api_host == "127.0.0.1"
        assert config.api_port == 9000


class TestContainer:
    def test_from_env_creates_container(self, monkeypatch):
        monkeypatch.delenv("TASKER_NEO4J_URI", raising=False)
        container = Container.from_env()
        assert container.config.neo4j.uri == "bolt://localhost:7687"

    def test_container_default_config(self):
        container = Container()
        assert container.config.neo4j.uri == "bolt://localhost:7687"

    def test_container_custom_config(self):
        neo4j_cfg = Neo4jConfig(uri="bolt://custom:7687")
        config = AppConfig(neo4j=neo4j_cfg)
        container = Container(config=config)
        assert container.config.neo4j.uri == "bolt://custom:7687"
