"""Neo4j driver connection management.

Handles driver initialization, connection pooling, health checks,
and graceful shutdown using the synchronous Neo4j driver.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from socialseed_tasker.storage.graph_database.queries import SCHEMA_CONSTRAINTS

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)


class SchemaError(Exception):
    """Raised when Neo4j schema is not properly initialized."""

    def __init__(self, message: str, missing_items: list[str] | None = None):
        super().__init__(message)
        self.missing_items = missing_items or []


class SchemaMigrationError(Exception):
    """Raised when schema migration fails."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class Neo4jDriver:
    """Manages the Neo4j driver lifecycle.

    Intent: Provide a single point of connection management for Neo4j.
    Business Value: Enables connection pooling, health monitoring, and
    clean shutdown without leaking resources.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "",
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._max_connection_lifetime = max_connection_lifetime
        self._driver: Driver | None = None
        self._schema_initialized = False
        self._schema_version: str = "1.0.0"

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
    def is_schema_ready(self) -> bool:
        """Check if schema has been initialized and verified."""
        return self._schema_initialized

    @property
    def schema_version(self) -> str:
        """Get the current schema version."""
        return self._schema_version

    def connect(self, force_schema_init: bool = False) -> None:
        """Initialize the Neo4j driver and verify connectivity.

        Creates the driver with connection pooling settings,
        verifies the connection, and initializes schema constraints.

        Args:
            force_schema_init: If True, reinitialize schema even if already initialized.
        """
        self._driver = GraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password),
            max_connection_lifetime=self._max_connection_lifetime,
        )
        self._verify_connection()

        if force_schema_init or not self._schema_initialized:
            self._init_schema()
            self._verify_schema(raise_on_failure=True)

        logger.info("Neo4j connection established to %s (schema: %s)", self._uri, self._schema_version)

    def close(self) -> None:
        """Gracefully shut down the Neo4j driver.

        Closes all connections in the pool and releases resources.
        """
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            self._schema_initialized = False
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

    def verify_schema(self) -> bool:
        """Public method to verify schema is properly initialized.

        Returns:
            True if all constraints and indexes exist.

        Raises:
            SchemaError: If schema is not properly initialized.
        """
        return self._verify_schema(raise_on_failure=True)

    def reinitialize_schema(self) -> bool:
        """Force reinitialization of schema constraints and indexes.

        This is useful when migrating to a new schema version or
        when schema verification fails.

        Returns:
            True if schema was successfully reinitialized.

        Raises:
            SchemaMigrationError: If migration fails.
        """
        logger.info("Forcing schema reinitialization...")

        errors: list[str] = []
        created: int = 0
        failed: int = 0

        with self._driver.session(database=self._database) as session:
            for constraint in SCHEMA_CONSTRAINTS:
                try:
                    result = session.run(constraint)
                    result.consume()
                    created += 1
                    logger.debug("Schema constraint applied: %s", constraint[:60])
                except Neo4jError as exc:
                    failed += 1
                    error_msg = str(exc)[:200]
                    errors.append(f"Failed: {constraint[:40]}... - {error_msg}")
                    logger.warning("Schema constraint failed: %s", error_msg)

        logger.info(f"Schema reinitialization complete: {created} created, {failed} failed")

        if failed > 0:
            raise SchemaMigrationError(f"Schema migration completed with {failed} errors", errors=errors)

        self._verify_schema(raise_on_failure=True)
        return True

    def get_schema_status(self) -> dict:
        """Get detailed schema status for debugging.

        Returns:
            Dictionary with constraint and index information.
        """
        constraints = []
        indexes = []

        with self._driver.session(database=self._database) as session:
            try:
                result = session.run("SHOW ALL CONSTRAINTS")
                for record in result:
                    constraints.append(
                        {
                            "name": record.get("name"),
                            "type": record.get("type"),
                            "labels": record.get("labelsOrTypes"),
                            "properties": record.get("properties"),
                        }
                    )
            except Neo4jError as exc:
                logger.warning("Failed to get constraints: %s", exc)

            try:
                result = session.run("SHOW ALL INDEXES")
                for record in result:
                    indexes.append(
                        {
                            "name": record.get("name"),
                            "type": record.get("type"),
                            "labels": record.get("labelsOrTypes"),
                            "properties": record.get("properties"),
                        }
                    )
            except Neo4jError as exc:
                logger.warning("Failed to get indexes: %s", exc)

        return {
            "initialized": self._schema_initialized,
            "version": self._schema_version,
            "constraints": constraints,
            "indexes": indexes,
            "database": self._database,
        }

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
        logger.info("Initializing Neo4j schema constraints...")

        created_count = 0
        skipped_count = 0

        with self._driver.session(database=self._database) as session:
            for constraint in SCHEMA_CONSTRAINTS:
                try:
                    result = session.run(constraint)
                    result.consume()
                    created_count += 1
                    logger.debug("Schema constraint applied: %s", constraint[:60])
                except Neo4jError as exc:
                    skipped_count += 1
                    logger.debug("Schema constraint already exists or skipped: %s", str(exc)[:100])

        logger.info(f"Schema initialization complete: {created_count} created, {skipped_count} skipped")

    def _verify_schema(self, raise_on_failure: bool = False) -> bool:
        """Verify all required constraints and indexes exist.

        Args:
            raise_on_failure: If True, raise SchemaError on missing constraints.

        Returns:
            True if all schema elements exist, False otherwise.
        """
        missing: list[str] = []

        required_constraints = {
            "issue_id": "Issue",
            "component_id": "Component",
        }

        required_indexes = {
            "issue_status": "Issue",
            "issue_component": "Issue",
            "issue_priority": "Issue",
        }

        with self._driver.session(database=self._database) as session:
            try:
                result = session.run("SHOW ALL CONSTRAINTS")
                existing_constraints: dict[str, dict] = {}
                for record in result:
                    name = record.get("name", "")
                    label = record.get("labelsOrTypes", "")
                    props = record.get("properties", [])
                    if label and props:
                        key = f"{label}:{props[0]}"
                        existing_constraints[key] = {"name": name, "label": label, "props": props}

                for constraint_name, label in required_constraints.items():
                    key = f"{label}:id"
                    if key not in existing_constraints:
                        missing.append(f"constraint: {constraint_name}")
            except Neo4jError as exc:
                logger.warning("Could not verify constraints: %s", exc)
                if raise_on_failure:
                    missing.append("constraint: unable to verify")

            try:
                result = session.run("SHOW ALL INDEXES")
                existing_indexes: set = set()
                for record in result:
                    name = record.get("name", "")
                    if name:
                        existing_indexes.add(name)

                for idx_name in required_indexes:
                    if idx_name not in existing_indexes:
                        missing.append(f"index: {idx_name}")
            except Neo4jError as exc:
                logger.warning("Could not verify indexes: %s", exc)
                if raise_on_failure:
                    missing.append("index: unable to verify")

        if missing and raise_on_failure:
            raise SchemaError(
                f"Neo4j schema not properly initialized. Missing: {', '.join(missing)}", missing_items=missing
            )

        self._schema_initialized = len(missing) == 0
        logger.info(
            "Schema verification result: %s",
            "READY" if self._schema_initialized else f"INCOMPLETE ({len(missing)} missing)",
        )
        return self._schema_initialized
