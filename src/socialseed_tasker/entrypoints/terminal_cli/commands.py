"""CLI command definitions for issue, dependency, and component management.

All commands delegate to core actions and use Rich for terminal output.
No business logic lives here - only presentation and user interaction.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

# Add src to path for imports when running as script
_src_path = str(Path(__file__).parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from socialseed_tasker.core.task_management.actions import (
    CircularDependencyError,
    ComponentNotFoundError,
    IssueNotFoundError,
    OpenDependenciesError,
    TaskRepositoryInterface,
    add_dependency_action,
    close_issue_action,
    create_issue_action,
    get_blocked_issues_action,
    get_dependency_chain_action,
    move_issue_action,
    remove_dependency_action,
)
from socialseed_tasker.core.task_management.entities import (
    Component,
    Issue,
    IssuePriority,
    IssueStatus,
)
from socialseed_tasker.storage.local_files.repositories import (
    FileTaskRepository,
)

console = Console()

# ---------------------------------------------------------------------------
# Repository factory
# ---------------------------------------------------------------------------

_data_dir = Path(".tasker-data")


def get_repository() -> TaskRepositoryInterface:
    """Create and return a file-based task repository.

    Intent: Provide the storage backend for CLI operations.
    Business Value: Allows CLI to work offline without Neo4j.
    """
    _data_dir.mkdir(parents=True, exist_ok=True)
    return FileTaskRepository(_data_dir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _format_issue_card(issue: Issue) -> Panel:
    """Format a single issue as a Rich panel card."""
    lines = [
        f"[bold]Status:[/bold] {_status_style(issue.status)}",
        f"[bold]Priority:[/bold] {_priority_style(issue.priority)}",
        f"[bold]Component:[/bold] {issue.component_id}",
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


def _issues_table(issues: list[Issue]) -> Table:
    """Format a list of issues as a Rich table."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title", width=40)
    table.add_column("Status", width=14)
    table.add_column("Priority", width=10)
    table.add_column("Component", width=38)

    for issue in issues:
        table.add_row(
            str(issue.id)[:8],
            issue.title,
            _status_style(issue.status),
            _priority_style(issue.priority),
            str(issue.component_id)[:8],
        )
    return table


def _components_table(components: list[Component]) -> Table:
    """Format a list of components as a Rich table."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", width=30)
    table.add_column("Project", width=30)
    table.add_column("Description", width=40)

    for comp in components:
        table.add_row(
            str(comp.id)[:8],
            comp.name,
            comp.project,
            comp.description or "",
        )
    return table


def _dependency_tree(issue_id: str, issues: list[Issue], label: str = "Dependencies") -> Tree:
    """Build a Rich tree showing dependency relationships."""
    tree = Tree(f"[bold]{label}[/bold] for {issue_id[:8]}")
    for dep in issues:
        tree.add(f"{str(dep.id)[:8]} - {dep.title} ({_status_style(dep.status)})")
    return tree


# ---------------------------------------------------------------------------
# Issue commands
# ---------------------------------------------------------------------------

issue_app = typer.Typer(help="Manage issues")


@issue_app.command("create")
def issue_create(
    title: str = typer.Argument(..., help="Issue title"),
    component: str = typer.Option(..., "--component", "-c", help="Component ID"),
    description: str = typer.Option("", "--description", "-d", help="Issue description"),
    priority: str = typer.Option("MEDIUM", "--priority", "-p", help="Priority: LOW, MEDIUM, HIGH, CRITICAL"),
    labels: str | None = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
) -> None:
    """Create a new issue."""
    repo = get_repository()
    label_list = [x.strip() for x in labels.split(",")] if labels else []

    try:
        issue = create_issue_action(
            repo,
            title=title,
            component_id=component,
            description=description,
            priority=priority,
            labels=label_list,
        )
        console.print(f"[success]Issue created:[/success] {issue.id}")
        console.print(_format_issue_card(issue))
    except ComponentNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(f"[error]Validation error: {exc}[/error]")
        raise typer.Exit(code=2) from exc


@issue_app.command("list")
def issue_list(
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    component: str | None = typer.Option(None, "--component", "-c", help="Filter by component ID"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List issues with optional filters."""
    repo = get_repository()
    status_filter = IssueStatus(status) if status else None

    issues = repo.list_issues(component_id=component, status=status_filter)

    if as_json:
        data = [issue.model_dump(mode="json") for issue in issues]
        console.print(json.dumps(data, indent=2))
        return

    if not issues:
        console.print("[info]No issues found.[/info]")
        return

    console.print(_issues_table(issues))


@issue_app.command("show")
def issue_show(issue_id: str) -> None:
    """Show detailed issue information."""
    repo = get_repository()
    issue = repo.get_issue(issue_id)

    if issue is None:
        console.print(f"[error]Issue '{issue_id}' not found.[/error]")
        raise typer.Exit(code=1) from None

    console.print(_format_issue_card(issue))

    # Show dependencies
    deps = repo.get_dependencies(issue_id)
    if deps:
        console.print(_dependency_tree(issue_id, deps, "Dependencies"))

    # Show dependents
    dependents = repo.get_dependents(issue_id)
    if dependents:
        console.print(_dependency_tree(issue_id, dependents, "Dependents"))


@issue_app.command("close")
def issue_close(issue_id: str) -> None:
    """Close an issue (validates no open dependencies)."""
    repo = get_repository()

    try:
        issue = close_issue_action(repo, issue_id)
        console.print(f"[success]Issue closed:[/success] {issue.id}")
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc
    except OpenDependenciesError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc


@issue_app.command("move")
def issue_move(
    issue_id: str,
    to_component: str = typer.Option(..., "--to", help="Target component ID"),
) -> None:
    """Move an issue to another component."""
    repo = get_repository()

    try:
        issue = move_issue_action(repo, issue_id, to_component)
        console.print(f"[success]Issue moved:[/success] {issue.id} -> component {to_component[:8]}")
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc
    except ComponentNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc


@issue_app.command("delete")
def issue_delete(
    issue_id: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an issue (with confirmation)."""
    repo = get_repository()
    issue = repo.get_issue(issue_id)

    if issue is None:
        console.print(f"[error]Issue '{issue_id}' not found.[/error]")
        raise typer.Exit(code=1) from None

    if not force:
        confirm = typer.confirm(f"Delete issue '{issue.title}' ({issue_id[:8]})?")
        if not confirm:
            console.print("[info]Cancelled.[/info]")
            return

    repo.delete_issue(issue_id)
    console.print(f"[success]Issue deleted:[/success] {issue_id[:8]}")


# ---------------------------------------------------------------------------
# Dependency commands
# ---------------------------------------------------------------------------

dependency_app = typer.Typer(help="Manage dependencies between issues")


@dependency_app.command("add")
def dependency_add(issue_id: str, depends_on: str) -> None:
    """Add a DEPENDS_ON relationship."""
    repo = get_repository()

    try:
        add_dependency_action(repo, issue_id, depends_on)
        console.print(f"[success]Dependency added:[/success] {issue_id[:8]} -> {depends_on[:8]}")
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc
    except CircularDependencyError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=2) from exc


@dependency_app.command("remove")
def dependency_remove(issue_id: str, depends_on: str) -> None:
    """Remove a DEPENDS_ON relationship."""
    repo = get_repository()

    try:
        remove_dependency_action(repo, issue_id, depends_on)
        console.print(f"[success]Dependency removed:[/success] {issue_id[:8]} -> {depends_on[:8]}")
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc


@dependency_app.command("list")
def dependency_list(issue_id: str) -> None:
    """List all dependencies and dependents for an issue."""
    repo = get_repository()
    issue = repo.get_issue(issue_id)

    if issue is None:
        console.print(f"[error]Issue '{issue_id}' not found.[/error]")
        raise typer.Exit(code=1) from None

    deps = repo.get_dependencies(issue_id)
    dependents = repo.get_dependents(issue_id)

    if deps:
        console.print(_dependency_tree(issue_id, deps, "Dependencies"))
    else:
        console.print("[info]No dependencies.[/info]")

    if dependents:
        console.print(_dependency_tree(issue_id, dependents, "Dependents"))
    else:
        console.print("[info]No dependents.[/info]")


@dependency_app.command("chain")
def dependency_chain(issue_id: str) -> None:
    """Show full transitive dependency chain."""
    repo = get_repository()

    try:
        chain = get_dependency_chain_action(repo, issue_id)
        if not chain:
            console.print("[info]No dependencies in chain.[/info]")
            return

        tree = Tree(f"[bold]Dependency chain[/bold] for {issue_id[:8]}")
        for i, dep in enumerate(chain):
            tree.add(f"{i+1}. {str(dep.id)[:8]} - {dep.title} ({_status_style(dep.status)})")
        console.print(tree)
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc


@dependency_app.command("blocked")
def dependency_blocked() -> None:
    """Show all issues blocked by open dependencies."""
    repo = get_repository()
    blocked = get_blocked_issues_action(repo)

    if not blocked:
        console.print("[success]No blocked issues.[/success]")
        return

    console.print("[warning]Blocked issues:[/warning]")
    console.print(_issues_table(blocked))


# ---------------------------------------------------------------------------
# Component commands
# ---------------------------------------------------------------------------

component_app = typer.Typer(help="Manage components")


@component_app.command("create")
def component_create(
    name: str = typer.Argument(..., help="Component name"),
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    description: str | None = typer.Option(None, "--description", "-d", help="Component description"),
) -> None:
    """Create a new component."""
    repo = get_repository()
    component = Component(name=name, project=project, description=description)
    repo.create_component(component)
    console.print(f"[success]Component created:[/success] {component.id}")


@component_app.command("list")
def component_list(
    project: str | None = typer.Option(None, "--project", "-p", help="Filter by project"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all components."""
    repo = get_repository()
    components = repo.list_components(project=project)

    if as_json:
        data = [c.model_dump(mode="json") for c in components]
        console.print(json.dumps(data, indent=2))
        return

    if not components:
        console.print("[info]No components found.[/info]")
        return

    console.print(_components_table(components))


@component_app.command("show")
def component_show(component_id: str) -> None:
    """Show component details and its issues."""
    repo = get_repository()
    component = repo.get_component(component_id)

    if component is None:
        console.print(f"[error]Component '{component_id}' not found.[/error]")
        raise typer.Exit(code=1) from None

    lines = [
        f"[bold]Name:[/bold] {component.name}",
        f"[bold]Project:[/bold] {component.project}",
        f"[bold]Created:[/bold] {component.created_at.isoformat()}",
    ]
    if component.description:
        lines.append(f"[bold]Description:[/bold] {component.description}")

    console.print(Panel("\n".join(lines), title=f"[bold]{component.name}[/bold] ({str(component.id)[:8]})", border_style="cyan"))

    # Show issues in this component
    issues = repo.list_issues(component_id=component_id)
    if issues:
        console.print("\n[bold]Issues:[/bold]")
        console.print(_issues_table(issues))
    else:
        console.print("\n[info]No issues in this component.[/info]")
