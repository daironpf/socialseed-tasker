"""CLI init command - scaffolds Tasker infrastructure into an external project.

Intent: Provide the 'tasker init' command that injects a pre-configured
tasker/ directory with AI skills, Docker infrastructure, and configuration
templates into any project.
Business Value: Enables one-command adoption of Tasker management in
external projects without manual setup.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.core.system_init.entities import FileOperation, ScaffoldStatus
from socialseed_tasker.core.system_init.scaffolder import ScaffolderService

console = Console(
    width=80,
    no_color=None,
    force_terminal=None,
    soft_wrap=False,
)

init_app = typer.Typer(
    help="Initialize Tasker infrastructure in an external project",
)


def _get_template_dir() -> Path:
    """Return the path to the bundled template assets."""
    return Path(__file__).parent.parent.parent / "assets" / "templates"


def scaffold_command(
    target: str = typer.Argument(
        ".",
        help="Target project directory (default: current directory)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files with latest templates",
    ),
    inplace: bool = typer.Option(
        False,
        "--inplace",
        "-i",
        help="Initialize in current directory without creating tasker/ subdirectory",
    ),
) -> None:
    """Scaffold Tasker infrastructure into a project.

    Creates a tasker/ directory with AI skills, Docker Compose,
    and configuration templates.

    Examples:
        tasker init                     # scaffold in current directory
        tasker init /path/to/project    # scaffold in specific directory
        tasker init --force             # overwrite existing templates
        tasker init --inplace          # scaffold in current directory (no subdir)
    """
    _run_scaffold(target, force, inplace)


@init_app.command()
def init(
    ctx: typer.Context,
    target: str = typer.Argument(
        ".",
        help="Target project directory (default: current directory)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files with latest templates",
    ),
    inplace: bool = typer.Option(
        False,
        "--inplace",
        "-i",
        help="Initialize in current directory without creating tasker/ subdirectory",
    ),
) -> None:
    """Scaffold Tasker infrastructure into a project.

    Creates a tasker/ directory with AI skills, Docker Compose,
    and configuration templates.

    Examples:
        tasker init                     # scaffold in current directory
        tasker init /path/to/project    # scaffold in specific directory
        tasker init --force             # overwrite existing templates
        tasker init --inplace          # scaffold in current directory (no subdir)
    """
    _run_scaffold(target, force, inplace)


def _run_scaffold(target: str, force: bool, inplace: bool = False) -> None:
    target_path = Path(target).resolve()

    if not target_path.exists():
        console.print(f"[error]Target directory does not exist: {target_path}[/error]")
        raise typer.Exit(code=1) from None

    if not target_path.is_dir():
        console.print(f"[error]Target is not a directory: {target_path}[/error]")
        raise typer.Exit(code=1) from None

    template_dir = _get_template_dir()
    if not template_dir.exists():
        console.print(
            f"[error]Template directory not found: {template_dir}\nThe installed package may be corrupted.[/error]"
        )
        raise typer.Exit(code=1) from None

    if inplace:
        output_path = target_path
    else:
        output_path = target_path / "tasker"
        if output_path.exists() and not force:
            console.print(f"[warning]Tasker directory already exists at: {output_path}[/warning]")
            console.print("Use [bold]--force[/bold] to overwrite existing templates.")
            raise typer.Exit(code=0)

    console.print(f"[info]Scaffolding Tasker into:[/info] [bold]{target_path}[/bold]")

    operations_log: list[FileOperation] = []

    def _on_progress(op: FileOperation) -> None:
        operations_log.append(op)
        rel_dest = op.destination.relative_to(target_path)
        if op.status == ScaffoldStatus.CREATED:
            console.print(f"  [success]Created:[/success]    {rel_dest}")
        elif op.status == ScaffoldStatus.OVERWRITTEN:
            console.print(f"  [warning]Overwritten:[/warning] {rel_dest}")
        elif op.status == ScaffoldStatus.SKIPPED:
            console.print(f"  [dim]Skipped:[/dim]      {rel_dest}")
        elif op.status == ScaffoldStatus.ERROR:
            console.print(f"  [error]Error:[/error]       {rel_dest} - {op.error_message}")

    service = ScaffolderService(template_dir, progress_callback=_on_progress)
    
    if inplace:
        result = service.scaffold(target_path, force=force, output_dir=target_path)
    else:
        result = service.scaffold(target_path, force=force)

    console.print()

    if result.success:
        summary = Table(show_header=False, box=None, padding=(0, 2))
        summary.add_row("[bold green]Scaffold complete![/bold green]", "")
        summary.add_row(f"  Files created:    {result.created_count}", "")
        if result.overwritten_count > 0:
            summary.add_row(f"  Files overwritten: {result.overwritten_count}", "")
        if result.skipped_count > 0:
            summary.add_row(f"  Files skipped:    {result.skipped_count}", "")
        console.print(summary)

        console.print()
        console.print(
            Panel(
                "[bold]Next steps:[/bold]\n"
                "  1. cd tasker && cp configs/.env.example configs/.env\n"
                "  2. Edit configs/.env with your settings\n"
                "  3. docker compose up -d\n"
                "  4. Import skills from tasker/skills/ in your AI agent",
                title="[cyan]Tasker Setup[/cyan]",
                border_style="cyan",
            )
        )
    else:
        console.print(f"[error]Scaffold completed with {result.error_count} error(s).[/error]")
        raise typer.Exit(code=1) from None
