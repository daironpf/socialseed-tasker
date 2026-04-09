"""Dependency injection container and configuration management.

Provides a central container for managing service lifecycles,
configuration loading from environment variables, and Neo4j database connection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
    from socialseed_tasker.storage.graph_database.driver import Neo4jDriver
    from socialseed_tasker.core.services.webhook_validator import WebhookSignatureValidator
    from socialseed_tasker.core.services.markdown_transformer import MarkdownTransformer
    from socialseed_tasker.core.services.secret_manager import SecretManager


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class Neo4jConnectionMode(str):
    """Connection mode for Neo4j.

    Intent: Distinguish between local Docker instances and remote Aura DB
    so the system can apply appropriate connection settings.
    Business Value: Enables seamless switching between development and
    production database environments.
    """

    LOCAL: str = "local"
    AURA: str = "aura"


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = ""
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    connection_mode: Neo4jConnectionMode = Neo4jConnectionMode.LOCAL

    @classmethod
    def from_uri(cls, uri: str, **kwargs: Any) -> Neo4jConfig:
        """Create configuration by inferring connection mode from URI.

        Args:
            uri: Neo4j connection string (bolt://, bolt+s://, neo4j://, etc.)
            **kwargs: Override any Neo4jConfig field.

        Returns:
            Neo4jConfig with inferred connection mode.
        """
        is_aura = uri.startswith(("bolt+s://", "neo4j+s://")) or "aura" in uri.lower()
        mode: Neo4jConnectionMode = Neo4jConnectionMode.AURA if is_aura else Neo4jConnectionMode.LOCAL
        return cls(uri=uri, connection_mode=mode, **kwargs)  # type: ignore[arg-type]


@dataclass
class AppConfig:
    """Application-wide configuration.

    Intent: Centralize all configuration so it can be loaded from
    environment variables and passed to components via DI.
    Business Value: Enables different configurations per environment
    (development, testing, production) without code changes.
    """

    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    policy_enforcement_mode: str = "warn"

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load configuration from environment variables.

        Environment variables override all defaults.
        """
        neo4j_uri = os.environ.get("TASKER_NEO4J_URI", "bolt://localhost:7687")
        neo4j = Neo4jConfig.from_uri(
            uri=neo4j_uri,
            user=os.environ.get("TASKER_NEO4J_USER", "neo4j"),
            password=os.environ.get("TASKER_NEO4J_PASSWORD", ""),
            database=os.environ.get("TASKER_NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=int(os.environ.get("TASKER_NEO4J_MAX_CONN_LIFETIME", "3600")),
        )
        enforcement_mode = os.environ.get("TASKER_POLICY_ENFORCEMENT_MODE", "warn")
        if enforcement_mode not in ("warn", "block", "disabled"):
            enforcement_mode = "warn"

        return cls(
            neo4j=neo4j,
            api_host=os.environ.get("TASKER_API_HOST", "0.0.0.0"),
            api_port=int(os.environ.get("TASKER_API_PORT", "8000")),
            debug=os.environ.get("TASKER_DEBUG", "").lower() in ("1", "true", "yes"),
            policy_enforcement_mode=enforcement_mode,
        )


# ---------------------------------------------------------------------------
# Container
# ---------------------------------------------------------------------------


class Container:
    """Dependency injection container.

    Intent: Manage service lifecycles and provide a single point of
    access to all application dependencies.
    Business Value: Enables testability (mock substitution), configurability
    (switch backends), and clear service boundaries.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()
        self._neo4j_driver: Neo4jDriver | None = None
        self._repository: TaskRepositoryInterface | None = None

    @property
    def config(self) -> AppConfig:
        return self._config

    @classmethod
    def from_env(cls) -> Container:
        """Create a container with configuration from environment variables."""
        return cls(config=AppConfig.from_env())

    def get_repository(self) -> TaskRepositoryInterface:
        """Get the task repository, initializing it if needed.

        Only Neo4j storage backend is supported.
        """
        if self._repository is None:
            driver = self._get_neo4j_driver()
            from socialseed_tasker.storage.graph_database.repositories import (
                Neo4jTaskRepository,
            )

            self._repository = Neo4jTaskRepository(driver)

        return self._repository

    def _get_neo4j_driver(self) -> Neo4jDriver:
        """Get or create the Neo4j driver."""
        if self._neo4j_driver is None:
            from socialseed_tasker.storage.graph_database.driver import Neo4jDriver

            neo4j_cfg = self._config.neo4j
            self._neo4j_driver = Neo4jDriver(
                uri=neo4j_cfg.uri,
                user=neo4j_cfg.user,
                password=neo4j_cfg.password,
                database=neo4j_cfg.database,
                max_connection_lifetime=neo4j_cfg.max_connection_lifetime,
            )
            self._neo4j_driver.connect()
        return self._neo4j_driver

    def initialize(self) -> None:
        """Initialize all services (eager initialization).

        Call this at application startup to verify all connections
        are working before serving requests.
        """
        self.get_repository()

    def cleanup(self) -> None:
        """Release all resources.

        Call this at application shutdown to close connections gracefully.
        """
        if self._neo4j_driver is not None:
            self._neo4j_driver.close()
            self._neo4j_driver = None
        self._repository = None

    def health_check(self) -> bool:
        """Verify the Neo4j database is accessible."""
        try:
            return self._get_neo4j_driver().health_check()
        except Exception:
            return False

    def get_webhook_validator(self) -> WebhookSignatureValidator:
        """Get the webhook signature validator."""
        from socialseed_tasker.core.services.webhook_validator import (
            WebhookSignatureValidator,
        )

        return WebhookSignatureValidator(secret=os.environ.get("GITHUB_WEBHOOK_SECRET", ""))

    def get_markdown_transformer(self) -> MarkdownTransformer:
        """Get the markdown transformer for analysis results."""
        from socialseed_tasker.core.services.markdown_transformer import (
            MarkdownTransformer,
        )

        return MarkdownTransformer()

    def get_secret_manager(self) -> SecretManager:
        """Get the secret manager for GitHub credentials."""
        from socialseed_tasker.core.services.secret_manager import (
            SecretManager,
        )

        return SecretManager()
