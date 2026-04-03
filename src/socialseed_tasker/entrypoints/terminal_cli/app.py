"""Typer CLI application entry point.

This module creates the main Typer application, configures Rich rendering,
registers command groups, and sets up error handling.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.theme import Theme

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
app.add_typer(init_app, name="init", help="Initialize Tasker in an external project")


@app.callback()
def main() -> None:
    """SocialSeed Tasker CLI.

    A graph-based task management framework for AI agents.
    """


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
