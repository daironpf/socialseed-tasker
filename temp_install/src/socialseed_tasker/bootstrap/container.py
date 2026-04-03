"""Dependency injection container and configuration management.

Provides a central container for managing service lifecycles,
configuration loading from environment variables, and storage backend selection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
    from socialseed_tasker.storage.graph_database.driver import Neo4jDriver


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = ""
    database: str = "neo4j"
    max_connection_lifetime: int = 3600


@dataclass
class StorageConfig:
    """Storage backend configuration."""

    backend: Literal["neo4j", "file"] = "file"
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    file_path: Path = Path(".tasker-data")


@dataclass
class AppConfig:
    """Application-wide configuration.

    Intent: Centralize all configuration so it can be loaded from
    environment variables and passed to components via DI.
    Business Value: Enables different configurations per environment
    (development, testing, production) without code changes.
    """

    storage: StorageConfig = field(default_factory=StorageConfig)
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables.

        Environment variables override all defaults.
        """
        neo4j = Neo4jConfig(
            uri=os.environ.get("TASKER_NEO4J_URI", "bolt://localhost:7687"),
            user=os.environ.get("TASKER_NEO4J_USER", "neo4j"),
            password=os.environ.get("TASKER_NEO4J_PASSWORD", ""),
            database=os.environ.get("TASKER_NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=int(
                os.environ.get("TASKER_NEO4J_MAX_CONN_LIFETIME", "3600")
            ),
        )

        storage_backend = os.environ.get("TASKER_STORAGE_BACKEND", "file")
        if storage_backend not in ("neo4j", "file"):
            raise ValueError(
                f"Invalid storage backend '{storage_backend}'. "
                f"Must be 'neo4j' or 'file'."
            )

        storage = StorageConfig(
            backend=storage_backend,  # type: ignore[arg-type]
            neo4j=neo4j,
            file_path=Path(os.environ.get("TASKER_FILE_PATH", ".tasker-data")),
        )

        return cls(
            storage=storage,
            api_host=os.environ.get("TASKER_API_HOST", "0.0.0.0"),
            api_port=int(os.environ.get("TASKER_API_PORT", "8000")),
            debug=os.environ.get("TASKER_DEBUG", "").lower() in ("1", "true", "yes"),
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
    def from_env(cls) -> "Container":
        """Create a container with configuration from environment variables."""
        return cls(config=AppConfig.from_env())

    def get_repository(self) -> "TaskRepositoryInterface":
        """Get the task repository, initializing it if needed.

        Selects the storage backend based on configuration.
        """
        if self._repository is None:
            backend = self._config.storage.backend

            if backend == "neo4j":
                driver = self._get_neo4j_driver()
                from socialseed_tasker.storage.graph_database.repositories import (
                    Neo4jTaskRepository,
                )

                self._repository = Neo4jTaskRepository(driver)
            else:
                from socialseed_tasker.storage.local_files.repositories import (
                    FileTaskRepository,
                )

                self._config.storage.file_path.mkdir(parents=True, exist_ok=True)
                self._repository = FileTaskRepository(self._config.storage.file_path)

        return self._repository

    def _get_neo4j_driver(self) -> "Neo4jDriver":
        """Get or create the Neo4j driver."""
        if self._neo4j_driver is None:
            from socialseed_tasker.storage.graph_database.driver import Neo4jDriver

            neo4j_cfg = self._config.storage.neo4j
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
        """Verify the storage backend is accessible."""
        try:
            backend = self._config.storage.backend
            if backend == "neo4j":
                return self._get_neo4j_driver().health_check()
            else:
                return self._config.storage.file_path.exists()
        except Exception:
            return False
