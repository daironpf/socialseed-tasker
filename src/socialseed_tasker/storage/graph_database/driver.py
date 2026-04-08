"""Neo4j driver connection management.

Handles driver initialization, connection pooling, health checks,
and graceful shutdown using the synchronous Neo4j driver.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from neo4j.exceptions import Neo4jError

from neo4j import GraphDatabase
from socialseed_tasker.storage.graph_database.queries import SCHEMA_CONSTRAINTS

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)


class Neo4jDriver:
    """Manages the Neo4j driver lifecycle.

    Intent: Provide a single point of connection management for Neo4j.
    Business Value: Enables connection pooling, health monitoring, and
    clean shutdown without leaking resources. Supports both local Docker
    instances and remote Neo4j Aura DB via bolt+s:// protocol.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "",
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
        encrypted: bool | None = None,
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._max_connection_lifetime = max_connection_lifetime
        self._driver: Driver | None = None
        self._encrypted = encrypted

    @property
    def driver(self) -> Driver:
        """Get the underlying Neo4j driver.

        Raises:
            RuntimeError: If the driver has not been initialized.
        """
        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self._driver

    @property
    def database(self) -> str:
        return self._database

    @property
    def uri(self) -> str:
        return self._uri

    def connect(self) -> None:
        """Initialize the Neo4j driver and verify connectivity.

        Creates the driver with connection pooling settings,
        verifies the connection, and initializes schema constraints.
        Automatically detects encryption from URI scheme:
        - bolt+s:// or neo4j+s:// → encrypted (Aura DB)
        - bolt:// or neo4j:// → unencrypted (local Docker)
        """
        driver_kwargs = {
            "max_connection_lifetime": self._max_connection_lifetime,
        }

        if self._encrypted is not None:
            driver_kwargs["encrypted"] = self._encrypted
        elif self._uri.startswith(("bolt+s://", "neo4j+s://")):
            driver_kwargs["encrypted"] = True

        self._driver = GraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password),
            **driver_kwargs,
        )
        self._verify_connection()
        self._init_schema()
        logger.info("Neo4j connection established to %s", self._uri)

    def close(self) -> None:
        """Gracefully shut down the Neo4j driver.

        Closes all connections in the pool and releases resources.
        """
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    def health_check(self) -> bool:
        """Verify the Neo4j connection is alive and responsive.

        Returns:
            True if the database responds to a simple query.
        """
        if self._driver is None:
            return False
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run("RETURN 1 AS ok")
                record = result.single()
                return record is not None and record["ok"] == 1
        except (Neo4jError, Exception):
            logger.exception("Neo4j health check failed")
            return False

    def _verify_connection(self) -> None:
        """Verify the driver can connect to the database."""
        try:
            with self._driver.session(database=self._database) as session:
                session.run("RETURN 1")
        except Neo4jError as exc:
            logger.error("Failed to connect to Neo4j: %s", exc)
            self.close()
            raise

    def _init_schema(self) -> None:
        """Create indexes and constraints if they don't exist."""
        with self._driver.session(database=self._database) as session:
            for constraint in SCHEMA_CONSTRAINTS:
                try:
                    session.run(constraint)
                except Neo4jError as exc:
                    logger.debug("Schema init notice: %s", exc)
