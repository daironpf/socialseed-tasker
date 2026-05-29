"""CLI command definitions for dependency management.

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

import typer
from rich.tree import Tree

from socialseed_tasker.application.actions import (
    CircularDependencyError,
    IssueNotFoundError,
    RemoteServiceError,
    add_dependency_action,
    get_blocked_issues_action,
    get_dependency_chain_action,
    remove_dependency_action,
)
from socialseed_tasker.cli.commands.shared import (
    console,
    get_repository,
    resolve_issue_id,
    _dependency_tree,
    _issues_table,
    _status_style,
)

dependency_app = typer.Typer(help="Manage dependencies between issues")


DEP_ADD_EPILOG = (
    "Examples:\n"
    "  tasker dependency add <issue_id> --depends-on <dep_id>\n"
    "  tasker dependency add <issue_id> <dep_id>\n"
    "  tasker dependency chain <issue_id>\n"
    "  tasker dependency add <issue_id> -d <dep_id> --force\n"
    "\n"
    "Tips:\n"
    "  - Use positional args: tasker dependency add A B  (A depends on B)\n"
    "  - Use --depends-on / -d explicitly: tasker dependency add A -d B\n"
    "  - Use --force to skip cycle validation (use with caution!)\n"
    "  - Use 'tasker issue list' to find issue IDs\n"
    "  - Use 'tasker dependency chain <issue_id>' to inspect dependency chains"
)

@dependency_app.command("add", epilog=DEP_ADD_EPILOG)
def dependency_add(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    depends_on: str = typer.Argument("", help="Issue ID this depends on (positional)"),
    depends_on_opt: str = typer.Option("", "--depends-on", "-d", help="Issue ID this depends on"),
    enforce: str = typer.Option("warn", "--enforce", "-e", help="Policy enforcement: warn, block, disabled"),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass cycle validation"),
) -> None:
    """Add a DEPENDS_ON relationship."""
    dep_id = depends_on_opt or depends_on
    if not dep_id:
        console.print("[error]Missing argument: DEPENDS_ON or --depends-on[/error]")
        raise typer.Exit(code=2)

    repo = get_repository()

    try:
        resolved_issue_id = resolve_issue_id(issue_id, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=2) from e

    try:
        resolved_dep_id = resolve_issue_id(dep_id, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=2) from e

    from socialseed_tasker.application.analyzer import ArchitecturalAnalyzer

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
    except RemoteServiceError as exc:
        console.print(f"[error]Service error:[/error] {exc}")
        raise typer.Exit(code=1) from exc


DEP_REMOVE_EPILOG = (
    "Examples:\n"
    "  tasker dependency remove <issue_id> --depends-on <dep_id>\n"
    "  tasker dependency remove <issue_id> <dep_id>\n"
    "\n"
    "Note: Use 'tasker dependency list <issue_id>' to see current dependencies."
)

@dependency_app.command("remove", epilog=DEP_REMOVE_EPILOG)
def dependency_remove(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    depends_on: str = typer.Argument("", help="Issue ID this depends on (positional)"),
    depends_on_opt: str = typer.Option("", "--depends-on", "-d", help="Issue ID this depends on"),
) -> None:
    """Remove a DEPENDS_ON relationship."""
    dep_id = depends_on_opt or depends_on
    if not dep_id:
        console.print("[error]Missing argument: DEPENDS_ON or --depends-on[/error]")
        raise typer.Exit(code=2)

    repo = get_repository()

    try:
        resolved_issue_id = resolve_issue_id(issue_id, repo)
        resolved_dep_id = resolve_issue_id(dep_id, repo)
        remove_dependency_action(repo, str(resolved_issue_id), str(resolved_dep_id))
        console.print(
            f"[success]Dependency removed:[/success] {str(resolved_issue_id)[:8]} -> {str(resolved_dep_id)[:8]}"
        )
    except (ValueError, IssueNotFoundError) as exc:
        console.print(f"[error]{exc}[/error]")
        raise typer.Exit(code=1) from exc
    except RemoteServiceError as exc:
        console.print(f"[error]Service error:[/error] {exc}")
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


DEP_CHAIN_EPILOG = (
    "Examples:\n"
    "  tasker dependency chain <issue_id>\n"
    "\n"
    "Note: Use 'tasker issue list' to find issue IDs."
)

@dependency_app.command("chain", epilog=DEP_CHAIN_EPILOG)
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
    except RemoteServiceError as exc:
        console.print(f"[error]Service error:[/error] {exc}")
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
