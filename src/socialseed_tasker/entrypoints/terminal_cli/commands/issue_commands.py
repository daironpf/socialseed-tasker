"""CLI command definitions for issue management.

All commands delegate to core actions and use Rich for terminal output.
No business logic lives here - only presentation and user interaction.

===============================================================================
KNOWN LIMITATION: CLI Blank Lines
===============================================================================
The CLI output may show extra blank lines at the start of commands. This is a
known issue with the Typer + Rich integration. The Rich Console is configured
with `force_terminal=True` which can cause additional newlines in some terminals.

Potential workarounds for future investigation:
1. Custom Rich Console configuration (adjusting output settings)
2. Alternative CLI framework migration (e.g., Click)
3. Rich render hooks modification

For most users, this is cosmetic and does not affect functionality.
===============================================================================
"""

from __future__ import annotations

import json
from uuid import UUID

import typer

from socialseed_tasker.core.task_management.actions import (
    ComponentNotFoundError,
    IssueNotFoundError,
    OpenDependenciesError,
    close_issue_action,
    create_issue_action,
    move_issue_action,
)
from socialseed_tasker.core.task_management.entities import IssueStatus
from socialseed_tasker.entrypoints.terminal_cli.commands.shared import (
    console,
    get_repository,
    resolve_component_id,
    resolve_issue_id,
    _dependency_tree,
    _format_issue_card,
    _issues_table,
    _status_style,
)

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
        console.print('[dim]Tip: Create an issue with: tasker issue create "Title" -c <component_id>[/dim]')
        return

    # Build component name lookup
    components = repo.list_components(project=project)
    component_names = {str(c.id): c.name for c in components}

    console.print(_issues_table(issues, component_names))
    console.print("[dim]Use -s OPEN to see only open issues, or -c <id> to filter by component[/dim]")


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
def issue_close(
    issue_id: str,
    affects: list[str] = typer.Option(None, "--affects", help="File paths affected by this issue"),
) -> None:
    """Close an issue (validates no open dependencies).

    Args:
        issue_id: Full UUID, short ID (8+ chars), or partial title match.

    Options:
        --affects: Optional list of file paths affected by this issue

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

        if affects:
            try:
                from socialseed_tasker.bootstrap.wiring import get_driver
                driver = get_driver()
                if driver:
                    from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository
                    code_repo = CodeGraphRepository(driver)
                    for file_path in affects:
                        result = code_repo.link_issue_to_file(resolved_id, file_path)
                        if result.get("success"):
                            console.print(f"[dim]  -> Linked to: {file_path}[/dim]")
            except Exception as e:
                console.print(f"[dim]  ⚠ Could not link files: {e}[/dim]")

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
