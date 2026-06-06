"""Status commands for CLI configuration and credentials."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel

from socialseed_tasker.cli.commands.shared import (
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
def status_command(
    short: bool = typer.Option(False, "--short", "-s", help="Show compact single-line summary"),
) -> None:
    """Show graph health dashboard with issue statistics."""
    from pathlib import Path

    from socialseed_tasker.application.container import AppConfig
    from socialseed_tasker.config.mode_config import DualModeConfig, _discover_config_file

    config = AppConfig.from_env()
    mode_cfg = DualModeConfig.load()
    cfg_path = _discover_config_file()

    conn_status = "connected"
    conn_error: str | None = None
    repo = get_repository()
    try:
        all_issues = repo.list_issues()
        components = repo.list_components()
    except Exception as exc:
        conn_status = "disconnected"
        conn_error = str(exc)
        all_issues = []
        components = []

    total_issues = len(all_issues)
    total_components = len(components)
    total_deps = sum(len(i.dependencies) for i in all_issues if i.dependencies)

    if short:
        console.print(
            f"[bold]Mode:[/bold] {mode_cfg.mode}  "
            f"[bold]API:[/bold] {mode_cfg.api_url}  "
            f"[bold]DB:[/bold] {conn_status}  "
            f"[bold]Issues:[/bold] {total_issues}  "
            f"[bold]Components:[/bold] {total_components}  "
            f"[bold]Deps:[/bold] {total_deps}"
        )
        return

    conn_status_display = f"[green]{conn_status}[/green]"

    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}

    for issue in all_issues:
        status = issue.status.value
        priority = issue.priority.value
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1

    from socialseed_tasker.application.actions import get_blocked_issues_action, get_workable_issues_action

    try:
        workable = get_workable_issues_action(repo, component_id=None)
    except Exception:
        workable = []

    try:
        blocked = get_blocked_issues_action(repo)
    except Exception:
        blocked = []

    console.print(
        Panel(
            f"[bold]Mode:[/bold] {mode_cfg.mode}\n"
            f"[bold]API URL:[/bold] {mode_cfg.api_url}\n"
            f"[bold]Config:[/bold] {cfg_path or '(none)'}\n"
            f"[bold]Backend:[/bold] neo4j (Graph)\n"
            f"[bold]Neo4j URI:[/bold] {config.neo4j.uri}\n"
            f"[bold]Database:[/bold] {config.neo4j.database}\n"
            f"[bold]Connection:[/bold] {conn_status_display}",
            title="[bold cyan]Tasker Status[/bold cyan]",
            border_style="cyan",
        )
    )

    if conn_error:
        console.print(f"[error]Connection error: {conn_error}[/error]")

    console.print()
    console.print(
        Panel(
            f"[bold]Components:[/bold] {total_components}\n"
            f"[bold]Total Issues:[/bold] {total_issues}\n"
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
    password: str = typer.Option(..., "--password", "--neo4j-password", "-pw", help="Neo4j password"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save credentials locally"),
) -> None:
    """Save credentials for future sessions.

    Allows you to store your Neo4j credentials locally so you don't
    need to enter them for every command.
    """
    import os

    from socialseed_tasker.cli.app import get_cli_container

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
