"""Application wiring and lifecycle management.

Wires together core, storage, and entrypoints at application startup.
Provides factory functions for both CLI and API entrypoints.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from socialseed_tasker.bootstrap.container import Container

load_dotenv()

if TYPE_CHECKING:
    from fastapi import FastAPI


def wire_api(config: Container | None = None) -> "FastAPI":
    """Create and configure the FastAPI application.

    Intent: Assemble the API with proper dependency injection and lifecycle hooks.
    Business Value: Single entry point for API initialization with configurable
    storage backend.

    Args:
        config: Optional container. Creates one from environment if not provided.

    Returns:
        Configured FastAPI application instance.
    """
    container = config or Container.from_env()

    from socialseed_tasker.entrypoints.web_api.app import create_app

    app = create_app(repository=container.get_repository())
    return app


def wire_cli(config: Container | None = None) -> None:
    """Run the CLI application.

    Intent: Initialize the CLI with proper dependency injection.
    Business Value: Single entry point for CLI initialization with configurable
    storage backend.

    Args:
        config: Optional container. Creates one from environment if not provided.
    """
    container = config or Container.from_env()
    container.initialize()

    from socialseed_tasker.entrypoints.terminal_cli.app import app

    try:
        app()
    finally:
        container.cleanup()
