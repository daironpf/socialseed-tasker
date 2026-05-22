from __future__ import annotations

import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
from rich.box import SIMPLE
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from socialseed_tasker.application.actions import (
    ComponentNotFoundError,
    IssueNotFoundError,
    TaskRepositoryInterface,
)
from socialseed_tasker.domain.entities import (
    Component,
    Issue,
    IssuePriority,
    IssueStatus,
)

console = Console(
    width=120,
    no_color=None,
    force_terminal=None,
    soft_wrap=False,
)

_CLI_CONFIG_FILE = Path.home() / ".tasker" / "credentials"


def _load_saved_credentials() -> dict[str, str]:
    config_file = _CLI_CONFIG_FILE
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _save_credentials(uri: str, user: str, password: str) -> None:
    config_file = _CLI_CONFIG_FILE
    config_file.parent.mkdir(parents=True, exist_ok=True)
    credentials = {
        "uri": uri,
        "user": user,
        "password": password,
    }
    with open(config_file, "w") as f:
        json.dump(credentials, f)


def _get_password_with_fallback() -> str:
    password = os.environ.get("TASKER_NEO4J_PASSWORD", "")
    if password:
        return password

    saved = _load_saved_credentials()
    if saved and saved.get("password"):
        uri = os.environ.get("TASKER_NEO4J_URI", "bolt://localhost:7687")
        if saved.get("uri") == uri:
            return saved.get("password", "")

    return ""


def get_repository() -> TaskRepositoryInterface:
    from socialseed_tasker.cli.app import get_cli_container

    password = _get_password_with_fallback()
    if password:
        os.environ["TASKER_NEO4J_PASSWORD"] = password

    if not password:
        console.print("[error]Error:[/error] Neo4j password is required.")
        console.print("[info]Please provide it via:[/info]")
        console.print("  - Environment variable: [bold]TASKER_NEO4J_PASSWORD[/bold]")
        console.print("  - CLI flag: [bold]--neo4j-password[/bold] or [bold]-pw[/bold]")
        console.print("")
        console.print("[info]Example:[/info]")
        console.print("  [bold]tasker -pw neoSocial component list[/bold]")
        raise typer.Exit(code=2)

    return get_cli_container().get_repository()


def resolve_component_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:
    try:
        return UUID(partial_id)
    except ValueError:
        pass

    if len(partial_id) < 4:
        raise ValueError(f"Invalid component ID format: {partial_id}. Need at least 4 characters.")

    try:
        comp = repo.get_component_by_name(partial_id)
        if comp:
            return comp.id
    except Exception:
        pass

    if len(partial_id) >= 8:
        components = repo.list_components(project=None)
        for comp in components:
            comp_id_str = str(comp.id)
            if comp_id_str.startswith(partial_id):
                return comp.id

    raise ValueError(f"Component not found: {partial_id}")


def resolve_issue_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:
    try:
        return UUID(partial_id)
    except ValueError:
        pass

    issues = repo.list_issues(status=None, project=None)

    for issue in issues:
        if issue.title.lower() == partial_id.lower():
            return issue.id

    if len(partial_id) < 4:
        raise ValueError(f"Invalid issue ID format: {partial_id}. Need at least 4 characters for UUID lookup.")

    for issue in issues:
        issue_id_str = str(issue.id)
        if issue_id_str.startswith(partial_id):
            return issue.id

    raise ValueError(f"Issue not found: {partial_id}")


_STATUS_COLORS = {
    IssueStatus.OPEN: "green",
    IssueStatus.IN_PROGRESS: "yellow",
    IssueStatus.CLOSED: "blue",
    IssueStatus.BLOCKED: "red",
}

_PRIORITY_COLORS = {
    IssuePriority.LOW: "dim white",
    IssuePriority.MEDIUM: "default",
    IssuePriority.HIGH: "bright_white",
    IssuePriority.CRITICAL: "bold bright_red",
}


def _status_style(status: IssueStatus) -> str:
    color = _STATUS_COLORS.get(status, "default")
    return f"[{color}]{status.value}[/{color}]"


def _priority_style(priority: IssuePriority) -> str:
    color = _PRIORITY_COLORS.get(priority, "default")
    return f"[{color}]{priority.value}[/{color}]"


def _format_issue_card(issue: Issue, component_name: str | None = None) -> Panel:
    comp_display = component_name if component_name else str(issue.component_id)[:8]
    lines = [
        f"[bold]Status:[/bold] {_status_style(issue.status)}",
        f"[bold]Priority:[/bold] {_priority_style(issue.priority)}",
        f"[bold]Component:[/bold] {comp_display}",
        f"[bold]Labels:[/bold] {', '.join(issue.labels) if issue.labels else 'none'}",
        f"[bold]Created:[/bold] {issue.created_at.isoformat()}",
    ]
    if issue.description:
        lines.append(f"\n{issue.description}")
    if issue.dependencies:
        lines.append(f"\n[bold]Dependencies:[/bold] {', '.join(str(d)[:8] for d in issue.dependencies)}")
    if issue.blocks:
        lines.append(f"[bold]Blocks:[/bold] {', '.join(str(b)[:8] for b in issue.blocks)}")
    if issue.architectural_constraints:
        lines.append(f"[bold]Constraints:[/bold] {', '.join(issue.architectural_constraints)}")

    return Panel("\n".join(lines), title=f"[bold]{issue.title}[/bold] ({str(issue.id)[:8]})", border_style="cyan")


def _issues_table(issues: list[Issue], component_names: dict[str, str] | None = None) -> Table:
    table = Table(show_header=True, header_style="bold cyan", box=SIMPLE, min_width=130)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title", width=40)
    table.add_column("Status", width=12)
    table.add_column("Priority", width=12)
    table.add_column("Component", width=40)

    for issue in issues:
        comp_id = str(issue.component_id)
        comp_name = (component_names or {}).get(comp_id, comp_id[:8])
        title = str(issue.title)[:40] if issue.title else ""
        table.add_row(
            str(issue.id)[:8],
            title,
            issue.status.value,
            issue.priority.value,
            comp_name,
        )
    return table


def _components_table(components: list[Component]) -> Table:
    table = Table(show_header=True, header_style="bold cyan", box=SIMPLE, min_width=100)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", min_width=20)
    table.add_column("Project", min_width=20)
    table.add_column("Description", min_width=30)

    for comp in components:
        table.add_row(
            str(comp.id)[:8],
            comp.name,
            comp.project,
            comp.description or "",
        )
    return table


def _dependency_tree(issue_id: str, issues: list[Issue], label: str = "Dependencies") -> Tree:
    tree = Tree(f"[bold]{label}[/bold] for {issue_id[:8]}")
    for dep in issues:
        tree.add(f"{str(dep.id)[:8]} - {dep.title} ({_status_style(dep.status)})")
    return tree
