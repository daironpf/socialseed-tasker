"""Status commands for CLI configuration and credentials."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel

from socialseed_tasker.entrypoints.terminal_cli.commands.shared import (
    _CLI_CONFIG_FILE,
    _save_credentials,
    console,
    get_repository,
)

# ---------------------------------------------------------------------------
# Status app (standalone, not under a subcommand group)
# ---------------------------------------------------------------------------

status_app = typer.Typer(help="Show CLI status and configuration")


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------


@status_app.command("status")
def status_command() -> None:
    """Show graph health dashboard with issue statistics."""
    from socialseed_tasker.bootstrap.container import AppConfig

    config = AppConfig.from_env()
    repo = get_repository()

    all_issues = repo.list_issues()
    components = repo.list_components()

    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}

    for issue in all_issues:
        status = issue.status.value
        priority = issue.priority.value
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1

    from socialseed_tasker.core.task_management.actions import get_blocked_issues_action, get_workable_issues_action

    workable = get_workable_issues_action(repo, component_id=None)
    blocked = get_blocked_issues_action(repo)

    total_deps = sum(len(i.dependencies) for i in all_issues if i.dependencies)

    console.print(
        Panel(
            f"[bold]Backend:[/bold] neo4j (Graph)\n"
            f"[bold]Neo4j URI:[/bold] {config.neo4j.uri}\n"
            f"[bold]Database:[/bold] {config.neo4j.database}\n"
            f"[bold]Connection:[/bold] {config.neo4j.connection_mode}",
            title="[bold cyan]Tasker Status[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print()
    console.print(
        Panel(
            f"[bold]Components:[/bold] {len(components)}\n"
            f"[bold]Total Issues:[/bold] {len(all_issues)}\n"
            f"[bold]Dependencies:[/bold] {total_deps}\n"
            f"[bold]Ready to Work:[/bold] {len(workable)}\n"
            f"[bold]Blocked:[/bold] {len(blocked)}",
            title="[bold cyan]Graph Health[/bold cyan]",
            border_style="green",
        )
    )

    console.print()
    console.print("[bold]By Status:[/bold]")
    for status, count in sorted(by_status.items()):
        color = f"status.{status.lower()}"
        console.print(f"  [{color}]{status}:[/{color}] {count}")

    console.print()
    console.print("[bold]By Priority:[/bold]")
    for priority, count in sorted(by_priority.items(), key=lambda x: -x[1]):
        color = f"priority.{priority.lower()}"
        console.print(f"  [{color}]{priority}:[/{color}] {count}")


@status_app.command("login")
def login_command(
    password: str = typer.Option(..., "--password", "-pw", help="Neo4j password"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save credentials locally"),
) -> None:
    """Save credentials for future sessions.

    Allows you to store your Neo4j credentials locally so you don't
    need to enter them for every command.
    """
    import os

    from socialseed_tasker.entrypoints.terminal_cli.app import get_cli_container

    uri = os.environ.get("TASKER_NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("TASKER_NEO4J_USER", "neo4j")

    os.environ["TASKER_NEO4J_PASSWORD"] = password

    try:
        repo = get_cli_container().get_repository()
        repo.list_components()

        if save:
            _save_credentials(uri, user, password)
            console.print("[success]Credentials saved successfully.[/success]")
        else:
            console.print("[success]Credentials valid for this session.[/success]")
    except Exception as e:
        console.print(f"[error]Authentication failed: {e}[/error]")
        raise typer.Exit(code=1) from None


@status_app.command("logout")
def logout_command() -> None:
    """Clear saved credentials."""
    config_file = _CLI_CONFIG_FILE
    if config_file.exists():
        config_file.unlink()
        console.print("[success]Credentials cleared.[/success]")
    else:
        console.print("[info]No saved credentials found.[/info]")


__all__ = ["status_app"]
