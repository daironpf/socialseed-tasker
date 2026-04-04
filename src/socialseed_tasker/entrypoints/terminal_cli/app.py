"""Typer CLI application entry point.

This module creates the main Typer application, configures Rich rendering,
registers command groups, and sets up error handling.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.theme import Theme

from socialseed_tasker.bootstrap.container import Container
from socialseed_tasker.entrypoints.cli.init_command import init_app
from socialseed_tasker.entrypoints.terminal_cli import commands

if TYPE_CHECKING:
    pass

# Custom Rich theme for consistent styling
cli_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "status.open": "green",
        "status.in_progress": "yellow",
        "status.closed": "blue",
        "status.blocked": "red",
        "priority.low": "dim white",
        "priority.medium": "default",
        "priority.high": "bright_white",
        "priority.critical": "bold bright_red",
    }
)

console = Console(theme=cli_theme)

# Global CLI state - shared container instance
_cli_container: Container | None = None


def get_cli_container() -> Container:
    """Get or create the global CLI container."""
    global _cli_container
    if _cli_container is None:
        _cli_container = Container.from_env()
    return _cli_container


def reset_cli_container() -> None:
    """Reset the CLI container (useful for testing)."""
    global _cli_container
    _cli_container = None


# Main application
app = typer.Typer(
    name="tasker",
    help="SocialSeed Tasker - A graph-based task management framework",
    add_completion=False,
    rich_markup_mode="rich",
)

# Register command groups
app.add_typer(commands.issue_app, name="issue", help="Manage issues")
app.add_typer(commands.dependency_app, name="dependency", help="Manage dependencies")
app.add_typer(commands.component_app, name="component", help="Manage components")
app.add_typer(commands.analyze_app, name="analyze", help="Analyze issues and root causes")

# Register init as a standalone command to avoid nested typer issues
from socialseed_tasker.entrypoints.cli.init_command import scaffold_command

app.command(name="init", help="Initialize Tasker in an external project")(scaffold_command)


# Register status as a standalone command (not a typer)
app.command(name="status", help="Show CLI status and configuration")(commands.status_command)


@app.callback()
def main(
    backend: str = typer.Option(
        "file",
        "--backend",
        "-b",
        help="Storage backend: 'file' or 'neo4j'",
        envvar="TASKER_STORAGE_BACKEND",
    ),
    file_path: str = typer.Option(
        ".tasker-data",
        "--file-path",
        "-f",
        help="Path for file-based storage",
        envvar="TASKER_FILE_PATH",
    ),
) -> None:
    """SocialSeed Tasker CLI.

    A graph-based task management framework for AI agents.
    """
    global _cli_container
    os.environ["TASKER_STORAGE_BACKEND"] = backend
    os.environ["TASKER_FILE_PATH"] = file_path
    _cli_container = None


def handle_error(error: Exception, exit_code: int = 1) -> None:
    """Display a user-friendly error message and exit.

    Intent: Present errors in a readable format without raw tracebacks.
    Business Value: Improves user experience and provides actionable guidance.
    """
    console.print(f"[error]Error:[/error] {error}")
    raise typer.Exit(code=exit_code) from error


def main_entry() -> None:
    """Entry point for the CLI script."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[warning]Operation cancelled.[/warning]")
        sys.exit(130)
    except Exception as exc:
        handle_error(exc)


if __name__ == "__main__":
    main_entry()
