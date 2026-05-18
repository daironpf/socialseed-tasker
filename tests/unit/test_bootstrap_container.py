"""Unit tests for bootstrap container."""

import pytest
from unittest.mock import MagicMock, patch

from socialseed_tasker.bootstrap.container import (
    Neo4jConfig,
    AppConfig,
    Neo4jConnectionMode,
    Container,
)


class TestNeo4jConfig:
    """Tests for Neo4jConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Neo4jConfig()
        
        assert config.uri == "bolt://localhost:7687"
        assert config.user == "neo4j"
        assert config.password == "neoSocial"
        assert config.database == "neo4j"
        assert config.connection_mode == Neo4jConnectionMode.LOCAL

    def test_from_uri_local(self):
        """Test from_uri detects local connection."""
        config = Neo4jConfig.from_uri("bolt://localhost:7687")
        
        assert config.connection_mode == Neo4jConnectionMode.LOCAL

    def test_from_uri_aura_bolt_plus(self):
        """Test from_uri detects Aura with bolt+s."""
        config = Neo4jConfig.from_uri("bolt+s://myinstance.databases.neo4j.io")
        
        assert config.connection_mode == Neo4jConnectionMode.AURA

    def test_from_uri_aura_neo4j_plus(self):
        """Test from_uri detects Aura with neo4j+s."""
        config = Neo4jConfig.from_uri("neo4j+s://myinstance.databases.neo4j.io")
        
        assert config.connection_mode == Neo4jConnectionMode.AURA

    def test_from_uri_with_password(self):
        """Test from_uri accepts password parameter."""
        config = Neo4jConfig.from_uri("bolt://localhost:7687", password="secret")
        
        assert config.password == "secret"

    def test_from_uri_aura_in_url(self):
        """Test from_uri detects aura in URL."""
        config = Neo4jConfig.from_uri("bolt://myinstance-aura.databases.neo4j.io")
        
        assert config.connection_mode == Neo4jConnectionMode.AURA


class TestAppConfig:
    """Tests for AppConfig class."""

    def test_default_values(self):
        """Test default AppConfig values."""
        config = AppConfig()
        
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8888
        assert config.debug is False
        assert config.policy_enforcement_mode == "warn"

    def test_with_neo4j_config(self):
        """Test AppConfig can have custom Neo4j config."""
        neo4j_config = Neo4jConfig(uri="bolt://custom:7687")
        config = AppConfig(neo4j=neo4j_config)
        
        assert config.neo4j.uri == "bolt://custom:7687"


class TestNeo4jConnectionMode:
    """Tests for Neo4jConnectionMode enum."""

    def test_connection_modes_exist(self):
        """Test both connection modes exist."""
        assert Neo4jConnectionMode.LOCAL == "local"
        assert Neo4jConnectionMode.AURA == "aura"


class TestContainer:
    """Tests for Container class."""

    def test_container_class_exists(self):
        """Test Container class exists."""
        assert Container is not None

    @patch.dict("os.environ", {
        "TASKER_NEO4J_URI": "bolt://test:7687",
        "TASKER_NEO4J_PASSWORD": "testpass"
    })
    def test_container_from_env(self):
        """Test Container can be created from environment."""
        container = Container.from_env()
        
        assert container is not None

    def test_container_has_config(self):
        """Test container has config attribute."""
        config = AppConfig(neo4j=Neo4jConfig())
        container = Container(config=config)
        
        assert hasattr(container, "config")