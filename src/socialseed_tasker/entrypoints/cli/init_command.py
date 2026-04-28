"""CLI init command - scaffolds Tasker infrastructure into an external project.

Intent: Provide the 'tasker init' command that injects a pre-configured
tasker/ directory with AI skills, Docker infrastructure, and configuration
templates into any project.
Business Value: Enables one-command adoption of Tasker management in
external projects without manual setup.
"""

from __future__ import annotations

from datetime import date
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


def _get_frontend_dir() -> Path:
    """Return the path to the bundled frontend build assets."""
    return Path(__file__).parent.parent.parent / "assets" / "frontend"


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
    project_name: str = typer.Option(
        None,
        "--project-name",
        "-pn",
        help="Project name for agent context",
    ),
    architecture: str = typer.Option(
        None,
        "--architecture",
        "-a",
        help="Architecture type: monolithic, microservices, serverless, api-first",
    ),
    language: str = typer.Option(
        None,
        "--language",
        "-lang",
        help="Programming language (e.g., python, go, typescript)",
    ),
    framework: str = typer.Option(
        None,
        "--framework",
        "-fw",
        help="Framework (e.g., fastapi, react, vue)",
    ),
    database: str = typer.Option(
        None,
        "--database",
        "-db",
        help="Database (e.g., postgresql, mongodb, neo4j)",
    ),
    github_repo: str = typer.Option(
        None,
        "--github-repo",
        "-gh",
        help="GitHub repository URL",
    ),
) -> None:
    """Scaffold Tasker infrastructure into a project.

    Creates a tasker/ directory with AI skills, Docker Compose,
    and configuration templates.

    Examples:
        tasker init                         # scaffold in current directory
        tasker init /path/to/project       # scaffold in specific directory
        tasker init --force               # overwrite existing templates
        tasker init --inplace            # scaffold in current directory (no subdir)
        tasker init -pn myapp -a api-first -lang python -fw fastapi -db postgresql
    """
    _run_scaffold(target, force, inplace, project_name, architecture, language, framework, database, github_repo)


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
    project_name: str = typer.Option(
        None,
        "--project-name",
        "-pn",
        help="Project name for agent context",
    ),
    architecture: str = typer.Option(
        None,
        "--architecture",
        "-a",
        help="Architecture type: monolithic, microservices, serverless, api-first",
    ),
    language: str = typer.Option(
        None,
        "--language",
        "-lang",
        help="Programming language (e.g., python, go, typescript)",
    ),
    framework: str = typer.Option(
        None,
        "--framework",
        "-fw",
        help="Framework (e.g., fastapi, react, vue)",
    ),
    database: str = typer.Option(
        None,
        "--database",
        "-db",
        help="Database (e.g., postgresql, mongodb, neo4j)",
    ),
    github_repo: str = typer.Option(
        None,
        "--github-repo",
        "-gh",
        help="GitHub repository URL",
    ),
) -> None:
    """Scaffold Tasker infrastructure into a project.

    Creates a tasker/ directory with AI skills, Docker Compose,
    and configuration templates.

    Examples:
        tasker init                         # scaffold in current directory
        tasker init /path/to/project       # scaffold in specific directory
        tasker init --force                # overwrite existing templates
        tasker init --inplace             # scaffold in current directory (no subdir)
        tasker init -pn myapp -a api-first -lang python -fw fastapi -db postgresql
    """
    _run_scaffold(target, force, inplace, project_name, architecture, language, framework, database, github_repo)


def _run_scaffold(
    target: str,
    force: bool,
    inplace: bool = False,
    project_name: str | None = None,
    architecture: str | None = None,
    language: str | None = None,
    framework: str | None = None,
    database: str | None = None,
    github_repo: str | None = None,
) -> None:
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

    service = ScaffolderService(template_dir, progress_callback=_on_progress, frontend_dir=_get_frontend_dir())

    if inplace:
        result = service.scaffold(target_path, force=force, output_dir=target_path)
    else:
        result = service.scaffold(target_path, force=force)

    if project_name or architecture or language or framework or database or github_repo:
        _fill_project_context(
            target_path if inplace else target_path / "tasker",
            project_name,
            architecture,
            language,
            framework,
            database,
            github_repo,
        )

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
                "  2. docker compose build tasker-api\n"
                "  3. docker compose up -d\n"
                "  4. Import skills from tasker/skills/ in your AI agent",
                title="[cyan]Tasker Setup[/cyan]",
                border_style="cyan",
            )
        )
    else:
        console.print(f"[error]Scaffold completed with {result.error_count} error(s).[/error]")
        raise typer.Exit(code=1) from None


def _fill_project_context(
    tasker_dir: Path,
    project_name: str | None,
    architecture: str | None,
    language: str | None,
    framework: str | None,
    database: str | None,
    github_repo: str | None,
) -> None:
    """Fill project.md template with user-provided values."""
    project_md = tasker_dir / "project.md"
    if not project_md.exists():
        return

    content = project_md.read_text(encoding="utf-8")

    replacements = {
        "{project_name}": project_name or "my-project",
        "{version}": "1.0.0",
        "{created_date}": date.today().isoformat(),
        "{architecture_type}": architecture or "api-first",
        "{language}": language or "python",
        "{framework}": framework or "fastapi",
        "{database}": database or "postgresql",
        "{frontend}": "vue",
        "{other_services}": "redis, celery",
        "{key_components}": "- API Gateway\n- Backend Service\n- Database",
        "{github_repo}": github_repo or "https://github.com/user/repo",
        "{default_branch}": "main",
        "{external_apis}": "- None configured",
        "{k_forbidden_technologies}": "- None",
        "{k_required_patterns}": "- Issues must have acceptance criteria",
        "{k_naming_conventions}": "kebab-case for files, CamelCase for classes",
        "{k_dependency_rules}": "- Max 10 direct dependencies per issue",
        "{setup_commands}": "pip install -r requirements.txt",
        "{test_commands}": "pytest tests/",
        "{build_commands}": "docker build .",
        "{code_review_count}": "1",
        "{agent_notes}": "- Read project.md before starting work",
        "{k_dos_and_donts}": "- DO: Use issue_quality_guide.json\n- DON'T: Create vague issues",
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    project_md.write_text(content, encoding="utf-8")
    console.print("  [success]Updated:[/success]    tasker/project.md")

    project_json = tasker_dir / "project.json"
    if not project_json.exists():
        return

    content = project_json.read_text(encoding="utf-8")

    replacements = {
        "{project_name}": project_name or "my-project",
        "{version}": "1.0.0",
        "{created_date}": date.today().isoformat(),
        "{architecture_type}": architecture or "api-first",
        "{language}": language or "python",
        "{framework}": framework or "fastapi",
        "{database}": database or "postgresql",
        "{frontend}": "vue",
        "{other_services}": "redis, celery",
        "{key_components}": '"API Gateway", "Backend Service", "Database"',
        "{github_repo}": github_repo or "https://github.com/user/repo",
        "{default_branch}": "main",
        "{setup_commands}": "pip install -r requirements.txt",
        "{test_commands}": "pytest tests/",
        "{build_commands}": "docker build .",
        "{code_review_count}": "1",
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    project_json.write_text(content, encoding="utf-8")
    console.print("  [success]Updated:[/success]    tasker/project.json")
