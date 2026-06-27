"""Configuration helper for Neo4j connection settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration loaded from environment variables."""

    uri: str
    user: str
    password: str
    max_retries: int
    retry_backoff: float


def load_config_from_env() -> Neo4jConfig:
    """Load Neo4j configuration from environment variables with defaults."""
    return Neo4jConfig(
        uri=os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("TASKER_NEO4J_USER", "neo4j"),
        password=os.getenv("TASKER_NEO4J_PASSWORD", "neoSocial"),
        max_retries=int(os.getenv("TASKER_NEO4J_MAX_RETRIES", "3")),
        retry_backoff=float(os.getenv("TASKER_NEO4J_RETRY_BACKOFF", "0.5")),
    )
