"""CLI command definitions for issue, dependency, and component management.

All commands delegate to core actions and use Rich for terminal output.
No business logic lives here - only presentation and user interaction.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

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

console = Console()

# ---------------------------------------------------------------------------
# Status app (standalone, not under a subcommand group)
# ---------------------------------------------------------------------------

status_app = typer.Typer(help="Show CLI status and configuration")


# ---------------------------------------------------------------------------
# Repository factory (uses Container from app.py)
# ---------------------------------------------------------------------------


def get_repository() -> TaskRepositoryInterface:
    """Get the task repository from the CLI container.

    Intent: Provide the storage backend for CLI operations, supporting
    both file and neo4j backends.
    Business Value: Unifies CLI and API to use the same configuration.
    """
    from socialseed_tasker.entrypoints.terminal_cli.app import get_cli_container

    return get_cli_container().get_repository()


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
    table = Table(show_header=True, header_style="bold cyan", min_width=120)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Title", width=30)
    table.add_column("Status", width=10)
    table.add_column("Priority", width=10)
    table.add_column("Component", width=36)

    for issue in issues:
        table.add_row(
            str(issue.id)[:8],
            issue.title,
            issue.status.value,
            issue.priority.value,
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
    issue_id: str = typer.Argument(..., help="Issue ID to move"),
    to_component: str = typer.Argument(..., help="Target component ID"),
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
            tree.add(f"{i + 1}. {str(dep.id)[:8]} - {dep.title} ({_status_style(dep.status)})")
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
    all: bool = typer.Option(False, "--all", "-a", help="Show all components from all projects"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all components."""
    repo = get_repository()
    if all:
        project = None
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

    console.print(
        Panel("\n".join(lines), title=f"[bold]{component.name}[/bold] ({str(component.id)[:8]})", border_style="cyan")
    )

    # Show issues in this component
    issues = repo.list_issues(component_id=component_id)
    if issues:
        console.print("\n[bold]Issues:[/bold]")
        console.print(_issues_table(issues))
    else:
        console.print("\n[info]No issues in this component.[/info]")


@component_app.command("update")
def component_update(
    component_id: str = typer.Argument(..., help="Component ID to update"),
    name: str | None = typer.Option(None, "--name", "-n", help="New component name"),
    description: str | None = typer.Option(None, "--description", "-d", help="New component description"),
    project: str | None = typer.Option(None, "--project", "-p", help="New project name"),
) -> None:
    """Update a component's fields."""
    from socialseed_tasker.core.task_management.actions import update_component_action

    if name is None and description is None and project is None:
        console.print(
            "[error]At least one field to update must be provided (--name, --description, --project).[/error]"
        )
        raise typer.Exit(code=1) from None

    repo = get_repository()
    try:
        updated = update_component_action(repo, component_id, name=name, description=description, project=project)
        console.print(f"[success]Component updated:[/success] {updated.name} ({updated.id})")
    except ComponentNotFoundError:
        console.print(f"[error]Component '{component_id}' not found.[/error]")
        raise typer.Exit(code=1) from None


@component_app.command("delete")
def component_delete(
    component_id: str = typer.Argument(..., help="Component ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion, issues become unassigned"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion without prompting"),
) -> None:
    """Delete a component."""
    from socialseed_tasker.core.task_management.actions import delete_component_action, ComponentHasIssuesError

    repo = get_repository()

    if not force and not yes:
        component = repo.get_component(component_id)
        if component:
            issues = repo.list_issues(component_id=component_id)
            if issues:
                console.print(
                    f"[warning]Component '{component_id}' has {len(issues)} issue(s).[/warning]\n"
                    f"Issues will become unassigned after deletion.\n"
                    f"Use [cyan]--force[/cyan] or [cyan]--yes[/cyan] to confirm, or [cyan]--force[/cyan] to delete anyway."
                )
                raise typer.Exit(code=1) from None

    try:
        delete_component_action(repo, component_id, force=True)
        console.print(f"[success]Component deleted:[/success] {component_id}")
    except ComponentNotFoundError:
        console.print(f"[error]Component '{component_id}' not found.[/error]")
        raise typer.Exit(code=1) from None
    except ComponentHasIssuesError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None
        raise typer.Exit(code=1) from None


# ---------------------------------------------------------------------------
# Analyze commands
# ---------------------------------------------------------------------------

analyze_app = typer.Typer(help="Analyze issues for root causes and impacts")


@analyze_app.command("root-cause")
def analyze_root_cause(
    test_name: str = typer.Option(..., "--test", "-t", help="Test name that failed"),
    error_message: str = typer.Option(..., "--error", "-e", help="Error message from test"),
    component: str = typer.Option("", "--component", "-c", help="Component where test failed"),
    labels: str | None = typer.Option(None, "--labels", "-l", help="Comma-separated test labels"),
) -> None:
    """Analyze test failure to find potential root causes in closed issues."""
    from socialseed_tasker.core.project_analysis.analyzer import RootCauseAnalyzer, TestFailure

    repo = get_repository()
    analyzer = RootCauseAnalyzer(repo)

    all_issues = repo.list_issues()
    closed_issues = [i for i in all_issues if i.status.value == "CLOSED"]

    if not closed_issues:
        console.print("[info]No closed issues found to analyze.[/info]")
        return

    test_failure = TestFailure(
        test_id="cli",
        test_name=test_name,
        error_message=error_message,
        component=component,
        labels=[x.strip() for x in labels.split(",")] if labels else [],
    )

    causal_links = analyzer.find_root_cause(test_failure, closed_issues)

    if not causal_links:
        console.print("[info]No potential root causes found.[/info]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Issue", width=40)
    table.add_column("Confidence", width=12)
    table.add_column("Reasons", width=40)

    for link in causal_links[:10]:
        table.add_row(
            f"{link.issue.title} ({str(link.issue.id)[:8]})",
            f"{link.confidence:.0%}",
            ", ".join(link.reasons[:2]),
        )

    console.print(Panel(table, title=f"[bold]Potential Root Causes ({len(causal_links)} found)[/bold]"))


@analyze_app.command("impact")
def analyze_impact(
    issue_id: str = typer.Argument(..., help="Issue ID to analyze"),
) -> None:
    """Analyze what other issues would be affected by this issue."""
    from socialseed_tasker.core.project_analysis.analyzer import RootCauseAnalyzer

    repo = get_repository()
    analyzer = RootCauseAnalyzer(repo)

    impact = analyzer.analyze_impact(issue_id)

    console.print(
        Panel(
            f"[bold]Directly affected:[/bold] {len(impact.directly_affected)} issues\n"
            f"[bold]Transitively affected:[/bold] {len(impact.transitively_affected)} issues\n"
            f"[bold]Blocked issues:[/bold] {len(impact.blocked_issues)} issues\n"
            f"[bold]Risk level:[/bold] {impact.risk_level.value}",
            title=f"[bold]Impact Analysis for {issue_id[:8]}[/bold]",
            border_style="cyan",
        )
    )

    if impact.directly_affected:
        console.print("\n[bold]Directly affected:[/bold]")
        for issue in impact.directly_affected:
            console.print(f"  - {issue.title} ({issue.status.value})")


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------


@status_app.command("status")
def status_command() -> None:
    """Show current CLI status, backend, and connection info."""
    from socialseed_tasker.bootstrap.container import AppConfig

    config = AppConfig.from_env()

    backend = config.storage.backend
    console.print(
        Panel(
            f"[bold]Backend:[/bold] {backend}\n"
            f"[bold]File path:[/bold] {config.storage.file_path}\n"
            f"[bold]Neo4j URI:[/bold] {config.storage.neo4j.uri}\n"
            f"[bold]Neo4j DB:[/bold] {config.storage.neo4j.database}",
            title="[bold]Tasker Status[/bold]",
            border_style="cyan",
        )
    )
