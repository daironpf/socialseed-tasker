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

if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass

import socialseed_tasker
from socialseed_tasker.application.actions import RemoteServiceError
from socialseed_tasker.application.container import Container
from socialseed_tasker.application.exceptions import GraphPortError
from socialseed_tasker.cli import commands


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
    width=120,
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
APP_EPILOG = (
    "Examples:\n"
    "  tasker issue create \"My title\" -c <id> --priority HIGH -l \"bug,frontend\"\n"
    "  tasker issue list --status OPEN --project my-proj\n"
    "  tasker component create \"auth-service\" -p \"my-project\"\n"
    "  tasker dependency add <issue_id> --depends-on <dep_id>\n"
    "  tasker dependency chain <issue_id>\n"
    "  tasker issue close <issue_id>\n"
    "\n"
    "Run 'tasker <command> --help' for detailed usage of each command."
)

app = typer.Typer(
    name="tasker",
    help="SocialSeed Tasker - A graph-based task management framework",
    add_completion=False,
    rich_markup_mode="rich",
    epilog=APP_EPILOG,
)

# Register command groups
app.add_typer(commands.issue_app, name="issue", help="Manage issues")
app.add_typer(commands.dependency_app, name="dependency", help="Manage dependencies")
app.add_typer(commands.component_app, name="component", help="Manage components")
app.add_typer(commands.analyze_app, name="analyze", help="Analyze issues and root causes")

# Register project detection command
app.add_typer(commands.project_app, name="project", help="Project detection and setup")

# Register init and install as standalone commands to avoid nested typer issues
from socialseed_tasker.cli.init_command import scaffold_command, interactive_init_command

app.command(name="install", help="Install Tasker infrastructure into a project (non-interactive)")(scaffold_command)
app.command(name="init", help="Initialize Tasker in a project interactively")(interactive_init_command)

# Register status as a standalone command (not a typer)
app.command(name="status", help="Show CLI status and configuration")(commands.status_command)

# Register login and logout as standalone commands
app.command(name="login", help="Save credentials for future sessions")(commands.login_command)
app.command(name="logout", help="Clear saved credentials")(commands.logout_command)

# Register seed command
app.add_typer(commands.seed_app, name="seed", help="Seed demo data for first-time users")

# Register code graph commands
app.add_typer(commands.code_graph_app, name="code-graph", help="Manage code graph analysis")

# Register RAG commands
app.add_typer(commands.rag_app, name="rag", help="RAG (Retrieval-Augmented Generation) commands")

# Register reasoning commands
app.add_typer(commands.reasoning_app, name="reasoning", help="AI Reasoning Log commands")

# Register agent commands
app.add_typer(commands.agent_app, name="agent", help="Agent Integration: context, suggestions, and reasoning")

# Register constraints commands
app.add_typer(commands.constraints_app, name="constraints", help="Manage project constraints and rules")

# Register storage commands
from socialseed_tasker.cli.cmd_storage import storage_app
app.add_typer(storage_app, name="storage")


def serve_command(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
) -> None:
    """Start the Tasker API server."""
    import uvicorn
    from socialseed_tasker.application.container import Container
    from socialseed_tasker.infrastructure.web_api.app import create_app

    console.print("[info]Starting Tasker API server...[/info]")

    container = Container.from_env()
    repository = container.get_repository()
    neo4j_driver = container.get_driver()
    app_api = create_app(repository, neo4j_driver)

    config = uvicorn.Config(
        app_api,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
    server = uvicorn.Server(config)
    server.run()


app.command(name="serve", help="Start the Tasker API server")(serve_command)


def restart_command(
    build: bool = typer.Option(True, "--build", "-b", help="Build images before starting"),
    force: bool = typer.Option(False, "--force", "-f", help="Force rebuild (--no-cache)"),
) -> None:
    """Restart Tasker services (build and start Docker containers)."""
    import subprocess

    console.print("[info]Restarting Tasker services...[/info]")

    agent_dir = ".agent"

    if build:
        console.print("[info]Building Docker images...[/info]")
        build_cmd = ["docker", "compose", "build"]
        if force:
            build_cmd.append("--no-cache")
        result = subprocess.run(build_cmd, cwd=agent_dir)
        if result.returncode != 0:
            console.print("[error]Docker build failed![/error]")
            raise typer.Exit(code=1)

    console.print("[info]Starting Docker containers...[/info]")
    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=agent_dir,
    )
    if result.returncode != 0:
        console.print("[error]Docker start failed![/error]")
        raise typer.Exit(code=1)

    console.print("[success]Tasker services restarted successfully![/success]")


app.command(name="restart", help="Restart Tasker Docker services")(restart_command)


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
        tasker issue create "Fix bug" -c <component_id> --priority HIGH
        tasker issue list --status OPEN --project myproj
        tasker dependency add <issue_id> --depends-on <dep_id>
        tasker issue close <issue_id>

    Common Workflow:
        1. tasker component create "auth-service" -p "my-project"
        2. tasker issue create "Implement login" -c <component_id> -p HIGH -l "backend,auth"
        3. tasker issue create "Add tests" -c <component_id>
        4. tasker issue show <issue_id>
        5. tasker dependency add <issue_id> --depends-on <dependency_id>
        6. tasker dependency chain <issue_id>

    Quick Start:
        1. Start Neo4j: docker compose up -d
        2. Seed demo data: tasker -pw neoSocial seed run
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
    if isinstance(error, GraphPortError):
        message = str(error)
        if "Neo4j operation failed" in message:
            console.print(f"[error]Database connection failed:[/error] {message}")
        else:
            console.print(f"[error]Database error:[/error] {message}")
    elif isinstance(error, RemoteServiceError):
        message = str(error)
        if "429" in message:
            console.print("[error]Rate limited:[/error] Too many requests. Please wait and try again.")
        elif "DATABASE_CONNECTION_ERROR" in message or "Connection error" in message:
            console.print(f"[error]Database connection failed:[/error] Check that Neo4j is running and accessible.")
        elif any(s in message for s in ("500", "502", "503")):
            console.print(f"[error]Service unavailable:[/error] {message}")
        else:
            console.print(f"[error]Service error:[/error] {message}")
    else:
        console.print(f"[error]Error:[/error] {error}")
    sys.exit(exit_code)


def main_entry() -> None:
    """Entry point for the CLI script."""
    try:
        app(standalone_mode=False)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        console.print("\n[warning]Operation cancelled.[/warning]")
        sys.exit(130)
    except Exception as exc:
        handle_error(exc)


if __name__ == "__main__":
    main_entry()
