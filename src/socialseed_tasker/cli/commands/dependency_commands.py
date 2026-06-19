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
from pathlib import Path

import typer
from rich.tree import Tree

from socialseed_tasker.application.actions import (
    CircularDependencyError,
    DuplicateDependencyError,
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
    except DuplicateDependencyError as exc:
        console.print(f"[warning]{exc}[/warning]")
        raise typer.Exit(code=0) from exc
    except RemoteServiceError as exc:
        console.print(f"[error]Service error:[/error] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[error]Unexpected error adding dependency:[/error] {exc}")
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


ADD_BATCH_EPILOG = (
    "Examples:\n"
    "  tasker dependency add-batch <issue_id> --depends-on <id1> --depends-on <id2>\n"
    "  tasker dependency add-batch <issue_id> --file deps.json\n"
    "  tasker dependency add-batch <issue_id> --deps <id1>,<id2>,<id3>\n"
    "\n"
    "File format (JSON):\n"
    '  {"depends_on_ids": ["id1", "id2", "id3"]}\n'
    "\n"
    "Tips:\n"
    "  - Batch mode uses the API bulk endpoint to avoid rate limit retries\n"
    "  - Each dependency is validated independently; failures don't rollback others\n"
    "  - Use --file to load dependency IDs from a JSON file"
)

@dependency_app.command("add-batch", epilog=ADD_BATCH_EPILOG)
def dependency_add_batch(
    issue_id: str = typer.Argument(..., help="Issue ID that depends on the listed issues"),
    depends_on: list[str] = typer.Option([], "--depends-on", "-d", help="Issue ID(s) this depends on (repeatable)"),
    deps: str = typer.Option("", "--deps", help="Comma-separated list of dependency IDs"),
    file: str = typer.Option("", "--file", "-f", help="JSON file with {\"depends_on_ids\": [...]}"),
) -> None:
    """Add multiple DEPENDS_ON relationships in batch (avoids rate-limit retries)."""
    dep_ids: list[str] = []

    if file:
        path = Path(file)
        if not path.exists():
            console.print(f"[error]File not found: {file}[/error]")
            raise typer.Exit(code=2)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            loaded = data.get("depends_on_ids", data if isinstance(data, list) else [])
            dep_ids.extend(loaded)
        except (json.JSONDecodeError, KeyError) as e:
            console.print(f"[error]Invalid JSON file: {e}[/error]")
            raise typer.Exit(code=2)

    if deps:
        dep_ids.extend(d.strip() for d in deps.split(",") if d.strip())

    dep_ids.extend(depends_on)

    if not dep_ids:
        console.print("[error]No dependency IDs provided.[/error]")
        console.print("[info]Provide them via --depends-on, --deps, or --file.[/info]")
        raise typer.Exit(code=2)

    repo = get_repository()

    try:
        resolved_issue_id = resolve_issue_id(issue_id, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        raise typer.Exit(code=2) from e

    resolved_str = str(resolved_issue_id)

    resolved_dep_ids: list[str] = []
    resolution_errors: list[dict] = []
    for raw_id in dep_ids:
        try:
            resolved = resolve_issue_id(raw_id, repo)
            resolved_dep_ids.append(str(resolved))
        except ValueError as e:
            resolution_errors.append({"depends_on_id": raw_id, "error": str(e)})

    if resolution_errors:
        for err in resolution_errors:
            console.print(f"[warning]Skipping unresolvable ID '{err['depends_on_id']}': {err['error']}[/warning]")

    if not resolved_dep_ids:
        console.print("[error]No valid dependency IDs could be resolved.[/error]")
        raise typer.Exit(code=2)

    bulk_method = getattr(repo, "add_dependencies_bulk", None)
    if bulk_method:
        result = bulk_method(resolved_str, resolved_dep_ids)
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)
        for r in result.get("results", []):
            if r.get("status") == "created":
                console.print(f"[success]Dependency added:[/success] {resolved_str[:8]} -> {r['depends_on_id'][:8]}")
            else:
                console.print(f"[error]Failed:[/error] {resolved_str[:8]} -> {r.get('depends_on_id', '?')[:8]} - {r.get('message', '')}")
    else:
        successful = 0
        failed = 0
        for dep_id in resolved_dep_ids:
            try:
                add_dependency_action(repo, resolved_str, dep_id)
                console.print(f"[success]Dependency added:[/success] {resolved_str[:8]} -> {dep_id[:8]}")
                successful += 1
            except (IssueNotFoundError, CircularDependencyError, DuplicateDependencyError) as exc:
                console.print(f"[error]Failed:[/error] {resolved_str[:8]} -> {dep_id[:8]} - {exc}")
                failed += 1
            except Exception as exc:
                console.print(f"[error]Failed:[/error] {resolved_str[:8]} -> {dep_id[:8]} - {exc}")
                failed += 1

    total = len(resolved_dep_ids)
    if failed:
        console.print(f"[warning]Batch complete: {successful}/{total} added, {failed} failed.[/warning]")
    else:
        console.print(f"[success]All {successful} dependencies added successfully.[/success]")
