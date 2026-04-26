"""Typer CLI application entry point.

This module creates the main Typer application, configures Rich rendering,
registers command groups, and sets up error handling.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import socialseed_tasker
import typer
from rich.console import Console
from rich.theme import Theme

from socialseed_tasker.bootstrap.container import Container
from socialseed_tasker.entrypoints.terminal_cli import commands


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        console.print(f"[info]socialseed-tasker {socialseed_tasker.__version__}[/info]")
        raise typer.Exit()


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

console = Console(
    theme=cli_theme,
    width=80,
    no_color=False,
    force_terminal=True,
    soft_wrap=False,
    highlight=False,
)

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

# Register project detection command
app.add_typer(commands.project_app, name="project", help="Project detection and setup")

# Register init as a standalone command to avoid nested typer issues
from socialseed_tasker.entrypoints.cli.init_command import scaffold_command

app.command(name="init", help="Initialize Tasker in an external project")(scaffold_command)

# Register status as a standalone command (not a typer)
app.command(name="status", help="Show CLI status and configuration")(commands.status_command)

# Register login and logout as standalone commands
app.command(name="login", help="Save credentials for future sessions")(commands.login_command)
app.command(name="logout", help="Clear saved credentials")(commands.logout_command)

# Register seed command
app.add_typer(commands.seed_app, name="seed", help="Seed demo data for first-time users")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version information",
        callback=version_callback,
        is_eager=True,
    ),
    neo4j_uri: str = typer.Option(
        "bolt://localhost:7687",
        "--neo4j-uri",
        help="Neo4j connection URI (default: bolt://localhost:7687)",
        envvar="TASKER_NEO4J_URI",
    ),
    neo4j_user: str = typer.Option(
        "neo4j",
        "--neo4j-user",
        "-u",
        help="Neo4j username (default: neo4j)",
        envvar="TASKER_NEO4J_USER",
    ),
    neo4j_password: str = typer.Option(
        "",
        "--neo4j-password",
        "-pw",
        help="Neo4j password (required)",
        envvar="TASKER_NEO4J_PASSWORD",
    ),
) -> None:
    """SocialSeed Tasker CLI.

    A graph-based task management framework for AI agents.
    Only Neo4j storage backend is supported.

    Examples:
        tasker --neo4j-password secret component create mycomp -p myproj
        tasker -pw secret issue create "Fix bug" -c <id>

    Quick Start:
        1. Start Neo4j: docker compose up -d
        2. Run: tasker -pw neoSocial seed run
        3. Open UI: http://localhost:8080

    📚 Docs: https://github.com/daironpf/socialseed-tasker#readme
    💬 Issues: https://github.com/daironpf/socialseed-tasker/issues
    """
    global _cli_container
    if neo4j_uri:
        os.environ["TASKER_NEO4J_URI"] = neo4j_uri
    if neo4j_user:
        os.environ["TASKER_NEO4J_USER"] = neo4j_user
    if neo4j_password:
        os.environ["TASKER_NEO4J_PASSWORD"] = neo4j_password
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
