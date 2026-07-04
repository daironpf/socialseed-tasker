from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.application.actions import (
    list_constraints_action,
    load_constraints_from_config_action,
    validate_constraints_action,
)
from socialseed_tasker.application.constraints import ConstraintConfig
from socialseed_tasker.cli.commands.shared import console, get_repository

constraints_app = typer.Typer(help="Manage project constraints and rules")


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
    config_file = Path(config_path)
    if not config_file.exists():
        console.print(f"[error]Config file not found: {Path(config_path).as_posix()}[/error]")
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
                    f"  [red]\u2022[/red] {v.message}\n"
                    f"    [dim]Resource:[/dim] {v.affected_resource}\n"
                    f"    [dim]Suggestion:[/dim] {v.suggestion}"
                )

        if result.soft_violations:
            console.print("\n[bold yellow]Soft Violations (require agent confirmation):[/bold yellow]")
            for v in result.soft_violations:
                console.print(f"  [yellow]\u2022[/yellow] {v.message}\n    [dim]Resource:[/dim] {v.affected_resource}")

        console.print(f"\n[bold]Summary:[/bold] {len(result.hard_violations)} hard, {len(result.soft_violations)} soft")


@constraints_app.command("doc-gaps")
def constraints_doc_gaps() -> None:
    """Find undocumented API endpoints (compare OpenAPI vs docs)."""
    from rich.table import Table
    import httpx

    try:
        openapi = httpx.get("http://localhost:8000/openapi.json", timeout=5).json()
    except Exception:
        console.print("[error]API not running[/error]")
        raise typer.Exit(code=1)

    try:
        doc = open("docs/API_REFERENCE.md", encoding="utf-8").read()
    except FileNotFoundError:
        console.print("[error]docs/API_REFERENCE.md not found[/error]")
        raise typer.Exit(code=1)

    gaps = []
    for path in openapi.get("paths", {}):
        if path not in doc:
            for method in openapi["paths"][path]:
                if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    gaps.append(f"{method.upper()} {path}")

    if not gaps:
        console.print("[info]All endpoints documented![/info]")
    else:
        t = Table(title=f"Doc Gaps ({len(gaps)})")
        t.add_column("Endpoint", style="cyan")
        for g in gaps[:15]:
            t.add_row(g)
        console.print(t)
