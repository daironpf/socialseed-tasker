"""CLI command definitions for issue, dependency, and component management.

All commands delegate to core actions and use Rich for terminal output.
No business logic lives here - only presentation and user interaction.

================================================================================
KNOWN LIMITATION: CLI Blank Lines
================================================================================
The CLI output may show extra blank lines at the start of commands. This is a
known issue with the Typer + Rich integration. The Rich Console is configured
with `force_terminal=True` which can cause additional newlines in some terminals.

Potential workarounds for future investigation:
1. Custom Rich Console configuration (adjusting output settings)
2. Alternative CLI framework migration (e.g., Click)
3. Rich render hooks modification

For most users, this is cosmetic and does not affect functionality.
================================================================================
"""

from __future__ import annotations

import json
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

console = Console(
    width=80,
    no_color=None,
    force_terminal=None,
    soft_wrap=False,
)

# ---------------------------------------------------------------------------
# Status app (standalone, not under a subcommand group)
# ---------------------------------------------------------------------------

status_app = typer.Typer(help="Show CLI status and configuration")

# ---------------------------------------------------------------------------
# Project detection app (detects modules from project structure)
# ---------------------------------------------------------------------------

project_app = typer.Typer(help="Detect project structure and create modules")


# ---------------------------------------------------------------------------
# Credentials persistence
# ---------------------------------------------------------------------------

_CLI_CONFIG_FILE = Path.home() / ".tasker" / "credentials"


def _load_saved_credentials() -> dict[str, str]:
    """Load saved credentials from local config file."""
    import json

    config_file = _CLI_CONFIG_FILE
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _save_credentials(uri: str, user: str, password: str) -> None:
    """Save credentials to local config file."""
    import json

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
    """Get password from env or saved credentials."""
    import os

    password = os.environ.get("TASKER_NEO4J_PASSWORD", "")
    if password:
        return password

    saved = _load_saved_credentials()
    if saved and saved.get("password"):
        uri = os.environ.get("TASKER_NEO4J_URI", "bolt://localhost:7687")
        if saved.get("uri") == uri:
            return saved.get("password", "")

    return ""


# ---------------------------------------------------------------------------
# Repository access
# ---------------------------------------------------------------------------


def get_repository() -> TaskRepositoryInterface:
    """Get the task repository for CLI operations.

    Intent: Provide the storage backend for CLI operations, supporting
    both file and neo4j backends.
    Business Value: Unifies CLI and API to use the same configuration.
    """
    import os

    from socialseed_tasker.entrypoints.terminal_cli.app import get_cli_container

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


# ---------------------------------------------------------------------------
# UUID Resolution Helpers
# ---------------------------------------------------------------------------


def resolve_component_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:
    """Resolve a partial component ID to a full UUID.

    Args:
        partial_id: Full UUID or partial (at least 4 characters) or name (exact match)
        repo: Task repository to search

    Returns:
        Full UUID

    Raises:
        ValueError: If ID format is invalid or not found
    """
    from uuid import UUID

    # Try full UUID first
    try:
        return UUID(partial_id)
    except ValueError:
        pass

    # Minimum 4 characters for partial lookup OR exact name match
    if len(partial_id) < 4:
        raise ValueError(f"Invalid component ID format: {partial_id}. Need at least 4 characters.")

    # Try to find by exact name match first (names can be short)
    try:
        comp = repo.get_component_by_name(partial_id)
        if comp:
            return comp.id
    except Exception:
        pass

    # Search for matching component by prefix (UUID-like patterns need 8+)
    if len(partial_id) >= 8:
        components = repo.list_components(project=None)
        for comp in components:
            comp_id_str = str(comp.id)
            if comp_id_str.startswith(partial_id):
                return comp.id

    raise ValueError(f"Component not found: {partial_id}")


def resolve_issue_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:
    """Resolve a partial issue ID to a full UUID.

    Args:
        partial_id: Full UUID, partial UUID (4+ chars), or title (any length)
        repo: Task repository to search

    Returns:
        Full UUID

    Raises:
        ValueError: If ID format is invalid or not found
    """
    from uuid import UUID

    # Try full UUID first
    try:
        return UUID(partial_id)
    except ValueError:
        pass

    # Get all issues once
    issues = repo.list_issues(status=None, project=None)

    # Try exact title match first (no length restriction - titles can be short)
    for issue in issues:
        if issue.title.lower() == partial_id.lower():
            return issue.id

    # Minimum 4 characters for partial UUID lookup
    if len(partial_id) < 4:
        raise ValueError(f"Invalid issue ID format: {partial_id}. Need at least 4 characters for UUID lookup.")

    # Search for matching issue by prefix (4+ chars)
    for issue in issues:
        issue_id_str = str(issue.id)
        if issue_id_str.startswith(partial_id):
            return issue.id

    raise ValueError(f"Issue not found: {partial_id}")


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


def _format_issue_card(issue: Issue, component_name: str | None = None) -> Panel:
    """Format a single issue as a Rich panel card."""
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
    """Format a list of issues as a Rich table."""
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
    """Format a list of components as a Rich table."""
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
    enforce: str = typer.Option("warn", "--enforce", "-e", help="Policy enforcement: warn, block, disabled"),
) -> None:
    """Create a new issue."""
    repo = get_repository()
    label_list = [x.strip() for x in labels.split(",")] if labels else []

    from uuid import uuid4

    from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer
    from socialseed_tasker.core.task_management.entities import Issue, IssuePriority, IssueStatus
    from socialseed_tasker.core.validation import (
        IssueDescriptionValidationError,
        IssueTitleValidationError,
        sanitize_issue_description,
        sanitize_issue_title,
        validate_issue_title,
    )

    try:
        validated_title = validate_issue_title(title)
    except IssueTitleValidationError as e:
        console.print(f"[error]Validation error: {e}[/error]")
        raise typer.Exit(code=2) from e

    try:
        sanitized_description = sanitize_issue_description(description)
    except IssueDescriptionValidationError as e:
        console.print(f"[error]Validation error: {e}[/error]")
        raise typer.Exit(code=2) from e

    sanitized_title = sanitize_issue_title(validated_title)

    try:
        component_uuid = resolve_component_id(component, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        console.print("[info]You can use full UUID, 8+ character prefix, or component name.[/info]")
        raise typer.Exit(code=2) from e

    normalized_priority = priority.upper()
    valid_priorities = [p.value for p in IssuePriority]
    if normalized_priority not in valid_priorities:
        console.print(f"[error]Invalid priority '{priority}'. Valid options: {', '.join(valid_priorities)}[/error]")
        raise typer.Exit(code=2)

    analyzer = ArchitecturalAnalyzer(repo)
    temp_issue = Issue(
        id=uuid4(),
        title=title,
        description=description,
        status=IssueStatus.OPEN,
        priority=IssuePriority(normalized_priority),
        component_id=str(component_uuid),
        labels=label_list,
    )
    result = analyzer.validate_issue_creation(temp_issue)
    if result.has_errors:
        console.print("[error]Policy violations found:[/error]")
        for v in result.violations:
            console.print(f"  - {v.rule_name}: {v.message}")
            if v.suggestion:
                console.print(f"    Suggestion: {v.suggestion}")
        if enforce == "block":
            console.print("[error]Blocking due to policy violations.[/error]")
            raise typer.Exit(code=1)
    elif result.has_warnings:
        console.print("[warning]Policy warnings:[/warning]")
        for v in result.violations:
            console.print(f"  - {v.rule_name}: {v.message}")

    try:
        issue, warnings = create_issue_action(
            repo,
            title=sanitized_title,
            component_id=str(component_uuid),
            description=sanitized_description,
            priority=normalized_priority,
            labels=label_list,
        )
        console.print(f"[success]Issue created:[/success] {issue.id}")
        comp = repo.get_component(str(component_uuid))
        console.print(_format_issue_card(issue, comp.name if comp else None))
        if warnings:
            for w in warnings:
                console.print(f"[warning]Warning:[/warning] {w}")
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
    project: str | None = typer.Option(None, "--project", "-p", help="Filter by project name"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List issues with optional filters."""
    repo = get_repository()
    status_filter = IssueStatus(status) if status else None

    issues = repo.list_issues(
        component_id=component, statuses=[status_filter] if status_filter else None, project=project
    )

    if as_json:
        data = [issue.model_dump(mode="json") for issue in issues]
        console.print(json.dumps(data, indent=2))
        return

    if not issues:
        console.print("[info]No issues found.[/info]")
        console.print('[dim]💡 Tip: Create an issue with: tasker issue create "Title" -c <component_id>[/dim]')
        return

    # Build component name lookup
    components = repo.list_components(project=project)
    component_names = {str(c.id): c.name for c in components}

    console.print(_issues_table(issues, component_names))
    console.print("[dim]💡 Use -s OPEN to see only open issues, or -c <id> to filter by component[/dim]")


@issue_app.command("show")
def issue_show(issue_id: str) -> None:
    """Show detailed issue information.

    Args:
        issue_id: Full UUID, short ID (8+ chars), or partial title match.

    Examples:
        tasker issue show 550e8400
        tasker issue show abc12345
        tasker issue show "Fix login"
    """
    from uuid import UUID

    repo = get_repository()

    resolved_id = issue_id
    try:
        UUID(issue_id)
    except ValueError:
        all_issues = repo.list_issues()
        matches = [issue for issue in all_issues if str(issue.id).startswith(issue_id)]

        if not matches:
            console.print(f"[error]Issue '{issue_id}' not found.[/error]")
            console.print("[dim]💡 Try: tasker issue list --status open[/dim]")
            raise typer.Exit(code=1) from None

        if len(matches) == 1:
            resolved_id = str(matches[0].id)
        else:
            console.print(f"[warning]Multiple matches for '{issue_id}':[/warning]")
            for m in matches:
                console.print(f"  - {m.title} ({m.id})")
            console.print("[dim]💡 Use full UUID to specify:[/dim]")
            console.print(f"[dim]  tasker issue show {matches[0].id}[/dim]")
            raise typer.Exit(code=1) from None

    issue = repo.get_issue(resolved_id)

    if issue is None:
        console.print(f"[error]Issue '{issue_id}' not found.[/error]")
        console.print("[dim]💡 Verify ID with: tasker issue list[/dim]")
        raise typer.Exit(code=1) from None

    # Resolve component name
    component = repo.get_component(str(issue.component_id))
    comp_name = component.name if component else None

    console.print(_format_issue_card(issue, comp_name))

    # Show dependencies
    deps = repo.get_dependencies(resolved_id)
    if deps:
        console.print(_dependency_tree(resolved_id, deps, "Dependencies"))

    # Show dependents
    dependents = repo.get_dependents(resolved_id)
    if dependents:
        console.print(_dependency_tree(resolved_id, dependents, "Dependents"))


@issue_app.command("close")
def issue_close(issue_id: str) -> None:
    """Close an issue (validates no open dependencies).

    Args:
        issue_id: Full UUID, short ID (8+ chars), or partial title match.

    Note:
        An issue cannot be closed if it has open dependencies. Resolve
        blocking issues first with: tasker dependency list <id>
    """
    from uuid import UUID

    repo = get_repository()

    resolved_id = issue_id
    try:
        UUID(issue_id)
    except ValueError:
        all_issues = repo.list_issues()
        for issue in all_issues:
            if str(issue.id).startswith(issue_id):
                resolved_id = str(issue.id)
                break
        else:
            console.print(f"[error]Issue '{issue_id}' not found.[/error]")
            console.print("[dim]💡 Check open issues: tasker issue list --status open[/dim]")
            raise typer.Exit(code=1) from None

    try:
        issue = close_issue_action(repo, resolved_id)
        console.print(f"[success]✓ Issue closed:[/success] {issue.title}")
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc
    except OpenDependenciesError as exc:
        console.print(f"[error]Cannot close:[/error] {exc}")
        console.print("[dim]💡 View dependencies: tasker dependency list[/dim]")
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
    from uuid import UUID

    repo = get_repository()

    resolved_id = issue_id
    try:
        UUID(issue_id)
    except ValueError:
        all_issues = repo.list_issues()
        for issue in all_issues:
            if issue.title.lower() == issue_id.lower() or issue_id.lower() in issue.title.lower():
                resolved_id = str(issue.id)
                break
        else:
            console.print(f"[error]Issue '{issue_id}' not found.[/error]")
            raise typer.Exit(code=1) from None

    issue = repo.get_issue(resolved_id)

    if issue is None:
        console.print(f"[error]Issue '{issue_id}' not found.[/error]")
        raise typer.Exit(code=1) from None

    if not force:
        confirm = typer.confirm(f"Delete issue '{issue.title}' ({resolved_id[:8]})?")
        if not confirm:
            console.print("[info]Cancelled.[/info]")
            return

    repo.delete_issue(resolved_id)
    console.print(f"[success]Issue deleted:[/success] {resolved_id[:8]}")


@issue_app.command("start")
def issue_start(
    issue_id: str,
    agent_id: str = typer.Option(..., "--agent-id", "-a", help="Agent identifier"),
) -> None:
    """Start agent work on an issue."""
    from uuid import UUID

    repo = get_repository()

    resolved_id = issue_id
    try:
        UUID(issue_id)
    except ValueError:
        all_issues = repo.list_issues()
        for issue in all_issues:
            if issue.title.lower() == issue_id.lower() or issue_id.lower() in issue.title.lower():
                resolved_id = str(issue.id)
                break
        else:
            console.print(f"[error]Issue '{issue_id}' not found.[/error]")
            raise typer.Exit(code=1)

    try:
        issue = repo.get_issue(resolved_id)
        if issue is None:
            console.print(f"[error]Issue '{issue_id}' not found.[/error]")
            raise typer.Exit(code=1)

        if hasattr(issue, "agent_working") and issue.agent_working:
            console.print(f"[error]Agent is already working on issue '{issue_id}'.[/error]")
            raise typer.Exit(code=1)

        repo.start_agent_work(resolved_id, agent_id)
        console.print(f"[success]Agent work started:[/success] {agent_id} on issue {resolved_id[:8]}")
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from e


@issue_app.command("finish")
def issue_finish(
    issue_id: str,
) -> None:
    """Finish agent work on an issue."""
    from uuid import UUID

    repo = get_repository()

    resolved_id = issue_id
    try:
        UUID(issue_id)
    except ValueError:
        all_issues = repo.list_issues()
        for issue in all_issues:
            if issue.title.lower() == issue_id.lower() or issue_id.lower() in issue.title.lower():
                resolved_id = str(issue.id)
                break
        else:
            console.print(f"[error]Issue '{issue_id}' not found.[/error]")
            raise typer.Exit(code=1)

    try:
        issue = repo.get_issue(resolved_id)
        if issue is None:
            console.print(f"[error]Issue '{issue_id}' not found.[/error]")
            raise typer.Exit(code=1)

        repo.finish_agent_work(resolved_id)
        console.print(f"[success]Agent work finished:[/success] issue {resolved_id[:8]}")
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from e


# ---------------------------------------------------------------------------
# Dependency commands
# ---------------------------------------------------------------------------

dependency_app = typer.Typer(help="Manage dependencies between issues")


@dependency_app.command("add")
def dependency_add(
    issue_id: str,
    depends_on: str,
    enforce: str = typer.Option("warn", "--enforce", "-e", help="Policy enforcement: warn, block, disabled"),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass cycle validation"),
) -> None:
    """Add a DEPENDS_ON relationship."""
    repo = get_repository()

    try:
        resolved_issue_id = resolve_issue_id(issue_id, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=2) from e

    try:
        resolved_dep_id = resolve_issue_id(depends_on, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=2) from e

    from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer

    issue_str = str(resolved_issue_id)
    dep_str = str(resolved_dep_id)

    if not force:
        analyzer = ArchitecturalAnalyzer(repo)
        result = analyzer.validate_dependency(issue_str, dep_str)
        if result.has_errors:
            console.print("[error]Policy violations found:[/error]")
            for v in result.violations:
                console.print(f"  - {v.rule_name}: {v.message}")
                if v.suggestion:
                    console.print(f"    Suggestion: {v.suggestion}")
            if enforce == "block":
                console.print("[error]Blocking due to policy violations.[/error]")
                raise typer.Exit(code=1)
        elif result.has_warnings:
            console.print("[warning]Policy warnings:[/warning]")
            for v in result.violations:
                console.print(f"  - {v.rule_name}: {v.message}")

    try:
        add_dependency_action(repo, issue_str, dep_str)
        console.print(f"[success]Dependency added:[/success] {issue_str[:8]} -> {dep_str[:8]}")
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc
    except CircularDependencyError as exc:
        console.print(f"[error]{exc}[/error]")
        if hasattr(exc, "cycle_path") and exc.cycle_path:
            console.print(f"[error]Cycle path: {' -> '.join(exc.cycle_path)}[/error]")
        raise typer.Exit(code=2) from exc


@dependency_app.command("remove")
def dependency_remove(issue_id: str, depends_on: str) -> None:
    """Remove a DEPENDS_ON relationship."""
    repo = get_repository()

    try:
        resolved_issue_id = resolve_issue_id(issue_id, repo)
        resolved_dep_id = resolve_issue_id(depends_on, repo)
        remove_dependency_action(repo, str(resolved_issue_id), str(resolved_dep_id))
        console.print(
            f"[success]Dependency removed:[/success] {str(resolved_issue_id)[:8]} -> {str(resolved_dep_id)[:8]}"
        )
    except IssueNotFoundError as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc


@dependency_app.command("list")
def dependency_list(
    issue_id: str,
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all dependencies and dependents for an issue."""
    repo = get_repository()

    try:
        resolved_id = resolve_issue_id(issue_id, repo)
        issue_id = str(resolved_id)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None

    issue = repo.get_issue(issue_id)

    if issue is None:
        console.print(f"[error]Issue '{issue_id}' not found.[/error]")
        raise typer.Exit(code=1) from None

    deps = repo.get_dependencies(issue_id)
    dependents = repo.get_dependents(issue_id)

    if as_json:
        data = {
            "dependencies": [d.model_dump(mode="json") for d in deps],
            "dependents": [d.model_dump(mode="json") for d in dependents],
        }
        console.print(json.dumps(data, indent=2))
        return

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
        resolved_id = resolve_issue_id(issue_id, repo)
        issue_id = str(resolved_id)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None

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

    # Build component name lookup
    components = repo.list_components()
    component_names = {str(c.id): c.name for c in components}

    console.print("[warning]Blocked issues:[/warning]")
    console.print(_issues_table(blocked, component_names))


# ---------------------------------------------------------------------------
# Component commands
# ---------------------------------------------------------------------------

component_app = typer.Typer(help="Manage components")


@component_app.command("create")
def component_create(
    name: str = typer.Argument(..., help="Component name"),
    project: str = typer.Option("default", "--project", "-p", help="Project name (default: 'default')"),
    description: str | None = typer.Option(None, "--description", "-d", help="Component description"),
) -> None:
    """Create a new component."""
    from socialseed_tasker.core.validation import (
        ComponentNameValidationError,
        sanitize_component_name,
        validate_component_name,
    )

    repo = get_repository()

    try:
        validated_name = validate_component_name(name)
    except ComponentNameValidationError as e:
        console.print(f"[error]Validation error: {e}[/error]")
        raise typer.Exit(code=2) from e

    sanitized_name = sanitize_component_name(validated_name)
    sanitized_description = sanitize_component_name(description or "")

    component = Component(name=sanitized_name, project=project, description=sanitized_description)
    repo.create_component(component)
    console.print(f"[success]Component '{sanitized_name}' created successfully (ID: {component.id})")


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
        console.print("[dim]💡 Tip: Create a component with: tasker component create <name> -p <project>[/dim]")
        return

    console.print(_components_table(components))
    console.print('[dim]💡 Next: Create issues with: tasker issue create "My Issue" -c <component>[/dim]')


@component_app.command("show")
def component_show(component: str) -> None:
    """Show component details and its issues."""
    repo = get_repository()

    try:
        component_uuid = resolve_component_id(component, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        console.print("[info]You can use full UUID, 8+ character prefix, or component name.[/info]")
        raise typer.Exit(code=2) from e

    component = repo.get_component(str(component_uuid))

    if component is None:
        console.print(f"[error]Component '{component}' not found.[/error]")
        raise typer.Exit(code=1)

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

    issues = repo.list_issues(component_id=str(component_uuid))
    if issues:
        console.print("\n[bold]Issues:[/bold]")
        console.print(_issues_table(issues, {str(component_uuid): component.name}))
    else:
        console.print("\n[info]No issues in this component.[/info]")


@component_app.command("update")
def component_update(
    component_id: str = typer.Argument(..., help="Component ID, name, or partial ID to update"),
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
        resolved_id = resolve_component_id(component_id, repo)
        updated = update_component_action(repo, str(resolved_id), name=name, description=description, project=project)
        console.print(f"[success]Component updated:[/success] {updated.name} ({updated.id})")
    except ComponentNotFoundError:
        console.print(f"[error]Component '{component_id}' not found.[/error]")
        raise typer.Exit(code=1) from None
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None


@component_app.command("delete")
def component_delete(
    component_id: str = typer.Argument(..., help="Component ID, name, or partial ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion, issues become unassigned"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion without prompting"),
) -> None:
    """Delete a component."""
    from socialseed_tasker.core.task_management.actions import ComponentHasIssuesError, delete_component_action

    repo = get_repository()

    try:
        resolved_id = resolve_component_id(component_id, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None

    if not force and not yes:
        component = repo.get_component(str(resolved_id))
        if component:
            issues = repo.list_issues(component_id=str(resolved_id))
            if issues:
                console.print(
                    f"[warning]Component '{component.name}' has {len(issues)} issue(s).[/warning]\n"
                    f"Issues will become unassigned after deletion.\n"
                    f"Use [cyan]--force[/cyan] or [cyan]--yes[/cyan] to confirm."
                )
                raise typer.Exit(code=1) from None

    try:
        delete_component_action(repo, str(resolved_id), force=True)
        console.print(f"[success]Component deleted:[/success] {resolved_id}")
    except ComponentNotFoundError:
        console.print(f"[error]Component '{component_id}' not found.[/error]")
        raise typer.Exit(code=1) from None
    except ComponentHasIssuesError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None

    if not force and not yes:
        component = repo.get_component(resolved_id)
        if component:
            issues = repo.list_issues(component_id=resolved_id)
            if issues:
                console.print(
                    f"[warning]Component '{component.name}' has {len(issues)} issue(s).[/warning]\n"
                    f"Issues will become unassigned after deletion.\n"
                    f"Use [cyan]--force[/cyan] or [cyan]--yes[/cyan] to confirm."
                )
                raise typer.Exit(code=1) from None

    try:
        delete_component_action(repo, resolved_id, force=True)
        console.print(f"[success]Component deleted:[/success] {resolved_id}")
    except ComponentNotFoundError:
        console.print(f"[error]Component '{component_id}' not found.[/error]")
        raise typer.Exit(code=1) from None
    except ComponentHasIssuesError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None


@component_app.command(name="add-dep")
def component_add_dependency(
    component_id: str = typer.Argument(..., help="Component that depends on another"),
    depends_on: str = typer.Option(..., "--depends-on", "-d", help="Component it depends on"),
) -> None:
    """Add a dependency between two components."""

    repo = get_repository()

    try:
        from socialseed_tasker.entrypoints.terminal_cli.commands import resolve_component_id

        source_id = resolve_component_id(component_id, repo)
        target_id = resolve_component_id(depends_on, repo)

        if str(source_id) == str(target_id):
            console.print("[error]A component cannot depend on itself.[/error]")
            raise typer.Exit(code=1)

        repo.add_component_dependency(str(source_id), str(target_id))
        console.print(f"[success]Added dependency:[/success] {component_id} → {depends_on}")
    except ComponentNotFoundError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None


@component_app.command(name="deps")
def component_list_dependencies(
    component_id: str = typer.Argument(..., help="Component to list dependencies for"),
) -> None:
    """List dependencies for a component."""
    from socialseed_tasker.entrypoints.terminal_cli.commands import resolve_component_id

    repo = get_repository()

    try:
        resolved_id = resolve_component_id(component_id, repo)

        deps = repo.get_component_dependencies(str(resolved_id))
        dependents = repo.get_component_dependents(str(resolved_id))

        console.print(f"\n[bold]Component:[/bold] {component_id}")
        console.print(f"\n[bold]Depends on ({len(deps)}):[/bold]")
        if deps:
            for d in deps:
                console.print(f"  → {d.name}")
        else:
            console.print("  (none)")

        console.print(f"\n[bold]Depended on by ({len(dependents)}):[/bold]")
        if dependents:
            for d in dependents:
                console.print(f"  ← {d.name}")
        else:
            console.print("  (none)")

    except ComponentNotFoundError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=1) from None
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
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
    issue_id: str = typer.Argument(..., help="Issue ID (full UUID, 4+ prefix, or exact title)"),
) -> None:
    """Analyze what other issues would be affected by this issue."""
    from socialseed_tasker.core.project_analysis.analyzer import RootCauseAnalyzer

    repo = get_repository()

    try:
        resolved_id = resolve_issue_id(issue_id, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        console.print("[info]You can use full UUID, 4+ character prefix, or exact title.[/info]")
        raise typer.Exit(code=2) from e

    analyzer = RootCauseAnalyzer(repo)
    impact = analyzer.analyze_impact(str(resolved_id))

    console.print(
        Panel(
            f"[bold]Directly affected:[/bold] {len(impact.directly_affected)} issues\n"
            f"[bold]Transitively affected:[/bold] {len(impact.transitively_affected)} issues\n"
            f"[bold]Blocked issues:[/bold] {len(impact.blocked_issues)} issues\n"
            f"[bold]Risk level:[/bold] {impact.risk_level.value}",
            title=f"[bold]Impact Analysis for {resolved_id}[/bold]",
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


# ---------------------------------------------------------------------------
# Project detection commands
# ---------------------------------------------------------------------------


@project_app.command("detect")
def project_detect(
    path: str = typer.Option(".", "--path", "-p", help="Project path to analyze"),
) -> None:
    """Detect project structure and list discovered modules.

    Scans the project directory to identify:
    - Microservices (from docker-compose.yml)
    - Packages (from package.json workspaces)
    - Python modules (from src/ directory)
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[error]Path does not exist: {project_path}[/error]")
        raise typer.Exit(code=1) from None

    discovered_modules: list[dict[str, Any]] = []

    docker_compose = project_path / "docker-compose.yml"
    if not docker_compose.exists():
        docker_compose = project_path / "docker-compose.yaml"

    if docker_compose.exists():
        try:
            import yaml  # type: ignore[import-untyped]

            with open(docker_compose) as f:
                compose_data = yaml.safe_load(f)
            if compose_data and "services" in compose_data:
                for service_name in compose_data["services"]:
                    discovered_modules.append(
                        {"name": service_name, "type": "microservice", "source": "docker-compose.yml"}
                    )
        except Exception as e:
            console.print(f"[warning]Could not parse docker-compose: {e}[/warning]")

    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            import json

            with open(package_json) as f:
                pkg_data = json.load(f)
            if "workspaces" in pkg_data:
                workspaces = pkg_data["workspaces"]
                base_path = project_path
                if isinstance(workspaces, list):
                    for ws in workspaces[:10]:
                        ws_path = ws.replace("*", "").replace("/", "")
                        if ws_path and (base_path / ws_path).exists():
                            discovered_modules.append(
                                {"name": ws.replace("*", ""), "type": "package", "source": "package.json"}
                            )
        except Exception as e:
            console.print(f"[warning]Could not parse package.json: {e}[/warning]")

    src_dir = project_path / "src"
    if not src_dir.exists():
        src_dir = project_path / "socialseed_tasker"
        if not src_dir.exists():
            src_dir = project_path / "src" / "socialseed_tasker"

    if src_dir.exists() and src_dir.name not in [m["name"] for m in discovered_modules]:
        has_submodules = False
        try:
            for item in src_dir.iterdir():
                if (
                    item.is_dir()
                    and not item.name.startswith("_")
                    and not item.name.startswith(".")
                    and item.name != "tests"
                    and not item.name.endswith(".egg-info")
                    and item.name != "socialseed_tasker"
                ):
                    init_file = item / "__init__.py"
                    pkg_json = item / "package.json"
                    if init_file.exists() or pkg_json.exists():
                        discovered_modules.append({"name": item.name, "type": "module", "source": "src/"})
                        has_submodules = True
        except Exception as e:
            console.print(f"[warning]Could not scan src/: {e}[/warning]")

        if not has_submodules:
            module_name = src_dir.name if src_dir.name != "socialseed_tasker" else project_path.name
            if module_name not in [m["name"] for m in discovered_modules]:
                discovered_modules.append({"name": module_name, "type": "module", "source": "src/"})

    pyproject = project_path / "pyproject.toml"
    if pyproject.exists() and not discovered_modules:
        try:
            import tomli

            with open(pyproject, "rb") as f:
                toml_data = tomli.load(f)
            if "tool" in toml_data and "poetry" in toml_data["tool"]:
                pkg = toml_data["tool"]["poetry"].get("packages", [])
                for p in pkg[:10]:
                    if isinstance(p, dict) and "path" in p:
                        discovered_modules.append(
                            {"name": p["path"].replace("./", ""), "type": "package", "source": "pyproject.toml"}
                        )
        except Exception as e:
            console.print(f"[warning]Could not parse pyproject.toml: {e}[/warning]")

    if not discovered_modules:
        console.print("[info]No modules detected. Using generic structure.[/info]")
        discovered_modules = [{"name": "src", "type": "code", "source": "default"}]

    table = Table(show_header=True, header_style="bold cyan", box=SIMPLE)
    table.add_column("Module Name", width=30)
    table.add_column("Type", width=15)
    table.add_column("Source", width=20)

    for module in discovered_modules:
        table.add_row(module["name"], module["type"], module["source"])

    console.print(Panel(table, title=f"[bold]Discovered Modules ({len(discovered_modules)})[/bold]"))


@project_app.command("setup")
def project_setup(
    path: str = typer.Option(".", "--path", "-p", help="Project path to analyze"),
    project_name: str = typer.Option(None, "--project", "-n", help="Project name (defaults to directory name)"),
    force: bool = typer.Option(False, "--force", "-f", help="Recreate all components"),
) -> None:
    """Create Tasker components for discovered project modules.

    This command:
    1. Detects project structure
    2. Creates a Tasker component for each discovered module
    3. Sets up proper project context
    """
    project_path = Path(path).resolve()
    if not project_path.exists():
        console.print(f"[error]Path does not exist: {project_path}[/error]")
        raise typer.Exit(code=1) from None

    proj_name = project_name or project_path.name
    console.print(f"[info]Setting up project:[/info] [bold]{proj_name}[/bold]")

    docker_compose = project_path / "docker-compose.yml"
    if not docker_compose.exists():
        docker_compose = project_path / "docker-compose.yaml"

    modules_to_create = []

    if docker_compose.exists():
        try:
            import yaml

            with open(docker_compose) as f:
                compose_data = yaml.safe_load(f)
            if compose_data and "services" in compose_data:
                for service_name in compose_data["services"]:
                    modules_to_create.append(
                        {
                            "name": service_name,
                            "description": f"{service_name.replace('-', ' ').replace('_', ' ').title()} microservice",
                            "labels": ["microservice", "service"],
                        }
                    )
        except Exception as e:
            console.print(f"[warning]Could not parse docker-compose: {e}[/warning]")

    if not modules_to_create:
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg_data = json.load(f)
                if "workspaces" in pkg_data:
                    workspaces = pkg_data["workspaces"]
                    if isinstance(workspaces, list):
                        for ws in workspaces[:10]:
                            pkg_name = ws.replace("*", "")
                            modules_to_create.append(
                                {
                                    "name": pkg_name,
                                    "description": f"{pkg_name} package",
                                    "labels": ["package", "workspace"],
                                }
                            )
            except Exception:
                pass

    if not modules_to_create:
        src_dir = project_path / "src"
        if not src_dir.exists():
            src_dir = project_path / "socialseed_tasker"
            if not src_dir.exists():
                src_dir = project_path / "src" / "socialseed_tasker"

        existing_names = [m["name"] for m in modules_to_create]
        if src_dir.exists() and src_dir.name not in existing_names:
            has_submodules = False
            try:
                for item in src_dir.iterdir():
                    if (
                        item.is_dir()
                        and not item.name.startswith("_")
                        and not item.name.startswith(".")
                        and item.name != "tests"
                        and not item.name.endswith(".egg-info")
                        and item.name != "socialseed_tasker"
                    ):
                        init_file = item / "__init__.py"
                        if init_file.exists():
                            modules_to_create.append(
                                {
                                    "name": item.name,
                                    "description": f"{item.name.title()} module",
                                    "labels": ["module", "python"],
                                }
                            )
                            has_submodules = True
            except Exception:
                pass

            if not has_submodules:
                module_name = src_dir.name if src_dir.name != "socialseed_tasker" else project_path.name
                if module_name not in existing_names:
                    modules_to_create.append(
                        {
                            "name": module_name,
                            "description": "Main package module",
                            "labels": ["module", "python"],
                        }
                    )

    if not modules_to_create:
        modules_to_create.append({"name": "main", "description": "Main application component", "labels": ["app"]})

    repo = get_repository()
    created_count = 0

    if force:
        existing = repo.list_components(project=proj_name)
        for comp in existing:
            with suppress(Exception):
                repo.delete_component(str(comp.id))

    for module in modules_to_create:
        existing = repo.list_components(project=proj_name)
        if any(c.name == module["name"] for c in existing):
            console.print(f"[dim]Skipping {module['name']} (already exists)[/dim]")
            continue

        try:
            from socialseed_tasker.core.task_management.entities import Component

            component = Component(name=module["name"], description=module["description"], project=proj_name)
            repo.create_component(component)
            console.print(f"[success]Created:[/success] {module['name']}")
            created_count += 1
        except Exception as e:
            console.print(f"[error]Failed to create {module['name']}: {e}[/error]")

    console.print(
        Panel(
            f"[bold]Setup complete![/bold]\nProject: {proj_name}\nComponents created: {created_count}",
            title="[bold]Project Setup[/bold]",
            border_style="cyan",
        )
    )


# ---------------------------------------------------------------------------
# Seed / Demo command
# ---------------------------------------------------------------------------

seed_app = typer.Typer(help="Seed demo data for first-time users")

# Constraints commands
# ---------------------------------------------------------------------------

constraints_app = typer.Typer(help="Manage project constraints and rules")

_SEED_COMPONENTS = [
    {"name": "api-gateway", "description": "Central API gateway routing requests to microservices"},
    {"name": "user-service", "description": "User authentication, profiles, and permissions"},
    {"name": "order-service", "description": "Order processing, state machine, and lifecycle"},
    {"name": "notification-service", "description": "Email, SMS, and push notification delivery"},
]

_SEED_ISSUES = [
    {
        "title": "Implement rate limiting on API gateway",
        "component": "api-gateway",
        "description": "Add token bucket rate limiting to prevent abuse. Configure per-endpoint limits.",
        "priority": "HIGH",
        "labels": ["security", "performance"],
    },
    {
        "title": "Add JWT token refresh endpoint",
        "component": "user-service",
        "description": "Create /auth/refresh endpoint to rotate access tokens without re-authentication.",
        "priority": "HIGH",
        "labels": ["auth", "security"],
    },
    {
        "title": "Implement user profile caching with Redis",
        "component": "user-service",
        "description": "Cache user profiles to reduce database load. Set TTL of 5 minutes.",
        "priority": "MEDIUM",
        "labels": ["performance", "caching"],
    },
    {
        "title": "Add order state machine with saga pattern",
        "component": "order-service",
        "description": "Implement distributed transaction handling using saga pattern for order creation.",
        "priority": "CRITICAL",
        "labels": ["architecture", "distributed-systems"],
    },
    {
        "title": "Create order cancellation workflow",
        "component": "order-service",
        "description": "Handle order cancellation with refund triggers and inventory restoration.",
        "priority": "HIGH",
        "labels": ["orders", "workflow"],
    },
    {
        "title": "Implement email notification templates",
        "component": "notification-service",
        "description": "Create HTML email templates for order confirmation, shipping, and delivery.",
        "priority": "MEDIUM",
        "labels": ["email", "templates"],
    },
    {
        "title": "Add SMS fallback for critical alerts",
        "component": "notification-service",
        "description": "When email delivery fails for critical notifications, fall back to SMS via Twilio.",
        "priority": "LOW",
        "labels": ["sms", "reliability"],
    },
    {
        "title": "Implement health check aggregation endpoint",
        "component": "api-gateway",
        "description": "Create /health endpoint that aggregates health status from all downstream services.",
        "priority": "MEDIUM",
        "labels": ["monitoring", "health"],
    },
]

_SEED_DEPENDENCIES = [
    # order-service saga depends on user-service auth
    ("Add order state machine with saga pattern", "Add JWT token refresh endpoint"),
    # order cancellation depends on saga
    ("Create order cancellation workflow", "Add order state machine with saga pattern"),
    # email templates needed for order confirmation
    ("Implement email notification templates", "Create order cancellation workflow"),
    # SMS fallback depends on email templates
    ("Add SMS fallback for critical alerts", "Implement email notification templates"),
    # health check depends on rate limiting
    ("Implement health check aggregation endpoint", "Implement rate limiting on API gateway"),
    # user profile caching depends on auth
    ("Implement user profile caching with Redis", "Add JWT token refresh endpoint"),
]


@seed_app.command("run")
def seed_run(
    force: bool = typer.Option(False, "--force", "-f", help="Delete existing demo data and re-seed"),
    project_name: str = typer.Option("demo-platform", "--project", "-p", help="Project name for seed data"),
) -> None:
    """Populate the database with demo components, issues, and dependencies.

    Creates a realistic microservices project with 4 components, 8 issues,
    and 6 dependency relationships to demonstrate the full dependency graph.
    """
    repo = get_repository()

    if force:
        existing = repo.list_components(project=project_name)
        for comp in existing:
            issues = repo.list_issues(component_id=str(comp.id))
            for issue in issues:
                with suppress(Exception):
                    repo.delete_issue(str(issue.id))
            with suppress(Exception):
                repo.delete_component(str(comp.id))
        console.print("[info]Cleared existing demo data.[/info]")

    existing_components = repo.list_components(project=project_name)
    if existing_components:
        console.print(f"[info]Demo data already exists for project '{project_name}'.[/info]")
        console.print("[info]Use [cyan]--force[/cyan] to re-seed.[/info]")
        return

    # Create components
    comp_map: dict[str, str] = {}
    for comp_data in _SEED_COMPONENTS:
        component = Component(name=comp_data["name"], project=project_name, description=comp_data["description"])
        repo.create_component(component)
        comp_map[comp_data["name"]] = str(component.id)
        console.print(f"[success]Component:[/success] {component.name}")

    # Create issues
    issue_map: dict[str, str] = {}
    for issue_data in _SEED_ISSUES:
        comp_id = comp_map[issue_data["component"]]
        issue, _ = create_issue_action(
            repo,
            title=issue_data["title"],
            component_id=comp_id,
            description=issue_data["description"],
            priority=issue_data["priority"],
            labels=issue_data["labels"],
        )
        issue_map[issue_data["title"]] = str(issue.id)
        console.print(f"  [dim]Issue:[/dim] {issue.title}")

    # Create dependencies
    for source_title, target_title in _SEED_DEPENDENCIES:
        source_id = issue_map[source_title]
        target_id = issue_map[target_title]
        add_dependency_action(repo, source_id, target_id)
        console.print(f"  [dim]Dependency:[/dim] {source_title[:40]}... -> {target_title[:40]}...")

    console.print(
        Panel(
            f"[bold]Demo data seeded successfully![/bold]\n\n"
            f"Project: {project_name}\n"
            f"Components: {len(_SEED_COMPONENTS)}\n"
            f"Issues: {len(_SEED_ISSUES)}\n"
            f"Dependencies: {len(_SEED_DEPENDENCIES)}\n\n"
            f"[bold]Try these commands:[/bold]\n"
            f"  tasker issue list --project {project_name}\n"
            f"  tasker dependency blocked\n"
            f"  tasker analyze impact <issue-id>",
            title="[bold]Seed Complete[/bold]",
            border_style="green",
        )
    )


# ---------------------------------------------------------------------------
# Constraints commands
# ---------------------------------------------------------------------------


@constraints_app.command("set")
def constraints_set(
    config_path: str = typer.Option(
        "tasker.constraints.yml",
        "--file",
        "-f",
        help="Path to constraints config file",
    ),
) -> None:
    """Load constraints from a YAML config file into Neo4j."""
    from pathlib import Path

    import yaml

    from socialseed_tasker.core.task_management.actions import load_constraints_from_config_action
    from socialseed_tasker.core.task_management.constraints import ConstraintConfig

    config_file = Path(config_path)
    if not config_file.exists():
        console.print(f"[error]Config file not found: {config_path}[/error]")
        raise typer.Exit(code=1)

    try:
        with open(config_file) as f:
            config_data = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[error]Failed to parse config file: {e}[/error]")
        raise typer.Exit(code=1) from e

    if not config_data:
        console.print("[warning]Config file is empty. No constraints to load.[/warning]")
        raise typer.Exit(code=0)

    repo = get_repository()

    constraint_config = ConstraintConfig(**config_data)
    result = load_constraints_from_config_action(repo, constraint_config)

    console.print(
        Panel(
            f"[bold]Constraints loaded successfully![/bold]\n\n"
            f"Created: {result['created']}\n"
            f"Deleted: {result['deleted']}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  tasker constraints list\n"
            f"  tasker constraints validate",
            title="[bold]Constraints Loaded[/bold]",
            border_style="green",
        )
    )


@constraints_app.command("list")
def constraints_list(
    category: str | None = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category (architecture, technology, naming, patterns, dependencies)",
    ),
) -> None:
    """List all active constraints."""
    from socialseed_tasker.core.task_management.actions import list_constraints_action

    repo = get_repository()

    constraints = list_constraints_action(repo, category=category)

    if not constraints:
        console.print("[info]No constraints found.[/info]")
        return

    table = Table(title="Active Constraints", show_header=True, header_style="bold cyan")
    table.add_column("Category", style="cyan")
    table.add_column("Level", style="yellow")
    table.add_column("Pattern/Service", style="green")
    table.add_column("Description")

    for c in constraints:
        table.add_row(
            c.category.value,
            c.level.value,
            c.pattern or c.service or c.from_layer or "-",
            c.description[:50] + "..." if len(c.description) > 50 else c.description,
        )

    console.print(table)
    console.print(f"\n[info]Total: {len(constraints)} constraints[/info]")


@constraints_app.command("validate")
def constraints_validate() -> None:
    """Validate constraints against current project state and report violations."""
    from socialseed_tasker.core.task_management.actions import validate_constraints_action

    repo = get_repository()

    result = validate_constraints_action(repo)

    if result.is_valid:
        console.print(
            Panel(
                "[bold green]All constraints are satisfied![/bold green]",
                title="Validation Result",
                border_style="green",
            )
        )
    else:
        if result.hard_violations:
            console.print("[bold red]Hard Violations:[/bold red]")
            for v in result.hard_violations:
                console.print(
                    f"  [red]•[/red] {v.message}\n"
                    f"    [dim]Resource:[/dim] {v.affected_resource}\n"
                    f"    [dim]Suggestion:[/dim] {v.suggestion}"
                )

        if result.soft_violations:
            console.print("\n[bold yellow]Soft Violations (require agent confirmation):[/bold yellow]")
            for v in result.soft_violations:
                console.print(f"  [yellow]•[/yellow] {v.message}\n    [dim]Resource:[/dim] {v.affected_resource}")

        console.print(f"\n[bold]Summary:[/bold] {len(result.hard_violations)} hard, {len(result.soft_violations)} soft")


# ---------------------------------------------------------------------------
# Code Graph commands
# ---------------------------------------------------------------------------

code_graph_app = typer.Typer(help="Code-as-Graph: scan and analyze source code")


@code_graph_app.command("scan")
def code_graph_scan(
    path: str = typer.Argument(..., help="Path to repository to scan"),
    incremental: bool = typer.Option(False, "--incremental", "-i", help="Only scan changed files"),
    git_aware: bool = typer.Option(True, "--git/--no-git", help="Use git to track changes"),
) -> None:
    """Scan a repository and extract code structure into the graph."""
    from socialseed_tasker.core.code_analysis.parser import CodeGraphParser
    from socialseed_tasker.bootstrap.wiring import get_driver

    console.print(f"[info]Scanning repository:[/info] {path}")

    parser = CodeGraphParser()

    try:
        files, symbols, imports, relationships = parser.scan_repository(
            repository_path=path,
            incremental=incremental,
            git_aware=git_aware,
        )

        console.print(f"[success]Found {len(files)} files, {len(symbols)} symbols, {len(imports)} imports[/success]")

        driver = get_driver()
        if driver:
            from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

            repo = CodeGraphRepository(driver)
            repo.save_scan_results(files, symbols, imports, relationships)
            console.print("[success]Saved to Neo4j graph[/success]")
        else:
            console.print("[warning]Neo4j not connected - results not saved[/warning]")

    except Exception as e:
        console.print(f"[error]Error scanning repository:[/error] {str(e)}")


@code_graph_app.command("find")
def code_graph_find(
    name: str = typer.Argument(..., help="Symbol name to search for"),
    symbol_type: str | None = typer.Option(None, "--type", "-t", help="Filter by symbol type"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
) -> None:
    """Find symbols by name in the code graph."""
    from socialseed_tasker.core.code_analysis.entities import SymbolType
    from socialseed_tasker.bootstrap.wiring import get_driver

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)

    sym_type = None
    if symbol_type:
        with suppress(ValueError):
            sym_type = SymbolType(symbol_type)

    results = repo.find_symbols(name=name, symbol_type=sym_type, limit=limit)

    if not results:
        console.print("[info]No symbols found[/info]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", width=30)
    table.add_column("Type", width=15)
    table.add_column("File", width=30)
    table.add_column("Line", width=8)

    for sym in results:
        table.add_row(
            sym.get("name", ""),
            sym.get("symbol_type", ""),
            "",
            str(sym.get("start_line", "")),
        )

    console.print(Panel(table, title=f"[bold]Symbols ({len(results)} found)[/bold]"))


@code_graph_app.command("files")
def code_graph_files(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results"),
    language: str | None = typer.Option(None, "--language", help="Filter by language"),
) -> None:
    """List files in the code graph."""
    from socialseed_tasker.bootstrap.wiring import get_driver

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)
    files = repo.get_files(limit=limit)

    if not files:
        console.print("[info]No files in graph[/info]")
        return

    if language:
        files = [f for f in files if f.get("language") == language]

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Path", width=50)
    table.add_column("Language", width=15)
    table.add_column("Lines", width=8)

    for f in files:
        table.add_row(
            f.get("path", ""),
            f.get("language", ""),
            str(f.get("lines_of_code", 0)),
        )

    console.print(Panel(table, title=f"[bold]Files ({len(files)} found)[/bold]"))


@code_graph_app.command("stats")
def code_graph_stats() -> None:
    """Show code graph statistics."""
    from socialseed_tasker.bootstrap.wiring import get_driver

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)
    stats = repo.get_stats()

    console.print(Panel(
        f"[bold]Total Files:[/bold] {stats.total_files}\n"
        f"[bold]Total Symbols:[/bold] {stats.total_symbols}\n"
        f"[bold]Total Relationships:[/bold] {stats.total_relationships}",
        title="[bold]Code Graph Statistics[/bold]",
    ))


@code_graph_app.command("clear")
def code_graph_clear(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion"),
) -> None:
    """Clear all code graph data from Neo4j."""
    from socialseed_tasker.bootstrap.wiring import get_driver

    if not confirm:
        console.print("[warning]Use --yes to confirm deletion[/warning]")
        return

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)
    repo.clear()
    console.print("[success]Code graph cleared[/success]")


# Create the main app with all command groups
app = typer.Typer()
app.add_typer(issue_app, name="issue")
app.add_typer(component_app, name="component")
app.add_typer(dependency_app, name="dependency")
app.add_typer(analyze_app, name="analyze")
app.add_typer(seed_app, name="seed")
app.add_typer(constraints_app, name="constraints")
app.add_typer(code_graph_app, name="code-graph")
