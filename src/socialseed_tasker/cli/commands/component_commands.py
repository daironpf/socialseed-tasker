"""CLI command definitions for component management.

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
from rich.panel import Panel

from socialseed_tasker.application.actions import (
    ComponentHasIssuesError,
    ComponentNotFoundError,
    delete_component_action,
    update_component_action,
)
from socialseed_tasker.domain.entities import Component
from socialseed_tasker.cli.commands.shared import (
    console,
    get_repository,
    resolve_component_id,
    _components_table,
    _issues_table,
)

component_app = typer.Typer(help="Manage components")


@component_app.command("create")
def component_create(
    name: str = typer.Argument(..., help="Component name"),
    project: str = typer.Option("default", "--project", "-p", help="Project name (default: 'default')"),
    description: str | None = typer.Option(None, "--description", "-d", help="Component description"),
) -> None:
    """Create a new component."""
    from socialseed_tasker.domain import (
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
        console.print("[dim]-> Tip: Create a component with: tasker component create <name> -p <project>[/dim]")
        return

    console.print(_components_table(components))
    console.print('[dim]-> Next: Create issues with: tasker issue create "My Issue" -c <component>[/dim]')


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
    from socialseed_tasker.application.actions import update_component_action

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
    from socialseed_tasker.application.actions import ComponentHasIssuesError, delete_component_action

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
        from socialseed_tasker.cli.commands.shared import resolve_component_id

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
    from socialseed_tasker.cli.commands.shared import resolve_component_id

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
