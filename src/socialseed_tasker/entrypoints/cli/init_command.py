"""CLI init command - scaffolds Tasker infrastructure into an external project.

Intent: Provide the 'tasker init' command that injects a pre-configured
.agent/ directory with AI skills, workflows, Docker infrastructure, and configuration
templates into any project.
Business Value: Enables one-command adoption of Tasker management in
external projects without manual setup.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import subprocess

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
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
        help="Initialize in current directory without creating .agent/ subdirectory",
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

    Creates a .agent/ directory with AI skills, workflows, Docker Compose,
    and configuration templates.

    Examples:
        tasker install                         # scaffold in current directory
        tasker install /path/to/project       # scaffold in specific directory
        tasker install --force               # overwrite existing templates
        tasker install --inplace            # scaffold in current directory (no subdir)
        tasker install -pn myapp -a api-first -lang python -fw fastapi -db postgresql
    """
    _run_scaffold(target, force, inplace, project_name, architecture, language, framework, database, github_repo)


def interactive_init_command(
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
        help="Initialize in current directory without creating .agent/ subdirectory",
    ),
) -> None:
    """Initialize Tasker in a project interactively.

    Prompts for project details before scaffolding.
    """
    console.print("[bold cyan]Welcome to SocialSeed Tasker Initialization[/bold cyan]")
    console.print("Please provide some details about your project to customize the AI agent configuration.\n")
    
    project_name = Prompt.ask("Project Name", default="my-project")
    architecture = Prompt.ask("Architecture (e.g. monolithic, microservices, api-first)", default="api-first")
    language = Prompt.ask("Primary Language", choices=["python", "typescript", "javascript", "go", "java", "rust", "other"], default="python")
    
    framework_map = {
        "python": ["fastapi", "django", "flask", "none"],
        "typescript": ["react", "vue", "next.js", "express", "nestjs", "none"],
        "javascript": ["react", "vue", "express", "none"],
        "go": ["gin", "echo", "fiber", "none"],
        "java": ["spring-boot", "quarkus", "micronaut", "jakarta-ee", "none"],
        "rust": ["actix", "rocket", "axum", "none"],
    }
    
    if language in framework_map:
        framework = Prompt.ask(f"Select Framework for {language}", choices=framework_map[language], default=framework_map[language][0])
    else:
        framework = Prompt.ask("Framework (e.g. react, vue, django)", default="none")
        
    database = Prompt.ask("Database (e.g. postgresql, mongodb, neo4j)", default="postgresql")
    github_repo = Prompt.ask("GitHub Repository URL", default="https://github.com/user/repo")
    
    slug = Prompt.ask("Project Slug", default=project_name.lower().replace(" ", "-"))
    description = Prompt.ask("Project Description", default=f"Tasker project for {project_name}")
    base_package = Prompt.ask("Base Package", default=project_name.lower().replace(" ", "_"))
    visibility = Prompt.ask("Visibility", choices=["PUBLIC", "PRIVATE"], default="PUBLIC")
    status = Prompt.ask("Project Status", default="DEVELOPMENT")
    tech_stack_str = Prompt.ask("Tech Stack (comma separated)", default=f"{language}, {framework}, {database}")
    main_stack_str = Prompt.ask("Main Stack (comma separated)", default=f"{language}, Neo4j")
    version = Prompt.ask("Version", default="0.1.0")
    conventions_url = Prompt.ask("Conventions URL", default="")
    conventions_rules = Prompt.ask("Conventions Rules", default="- Use standard conventions")
    global_status = Prompt.ask("Global Status", choices=["DEVELOPMENT", "STAGING", "PRODUCTION"], default="DEVELOPMENT")
    
    console.print("\n[bold cyan]User Configuration (Human-in-the-Loop)[/bold cyan]")
    username = Prompt.ask("Username", default="admin")
    email = Prompt.ask("Email", default="admin@example.com")
    user_role = Prompt.ask("Role", choices=["ADMIN", "LEAD_ARCHITECT", "DEVELOPER"], default="ADMIN")
    github_handle = Prompt.ask("GitHub Handle", default="admin")
    
    tech_stack = [s.strip() for s in tech_stack_str.split(",") if s.strip()]
    main_stack = [s.strip() for s in main_stack_str.split(",") if s.strip()]
    
    console.print("\n[bold cyan]Project Policies & Constraints[/bold cyan]")
    forbidden_tech = Prompt.ask("Forbidden Technologies (e.g. jQuery, var)", default="- None")
    required_patterns = Prompt.ask("Required Patterns (e.g. Issues must have acceptance criteria)", default="- Issues must have acceptance criteria")
    naming_conventions = Prompt.ask("Naming Conventions (e.g. kebab-case for files)", default="kebab-case for files, CamelCase for classes")
    dependency_rules = Prompt.ask("Dependency Rules (e.g. Max 10 direct dependencies)", default="- Max 10 direct dependencies per issue")
    dos_and_donts = Prompt.ask("Do's and Don'ts", default="- DO: Use .agent/skills/issue_quality_guide.json\n- DON'T: Create vague issues")
    
    console.print("\n[info]Starting initialization with provided context...[/info]\n")
    
    _run_scaffold(
        target=target,
        force=force,
        inplace=inplace,
        project_name=project_name,
        architecture=architecture,
        language=language,
        framework=framework,
        database=database,
        github_repo=github_repo,
        forbidden_tech=forbidden_tech,
        required_patterns=required_patterns,
        naming_conventions=naming_conventions,
        dependency_rules=dependency_rules,
        dos_and_donts=dos_and_donts,
        interactive=True,
    )

    console.print("\n[info]Starting Tasker infrastructure via Docker Compose...[/info]")
    try:
        compose_dir = Path(target).resolve()
        if not inplace:
            compose_dir = compose_dir / ".agent" / "tasker"
            
        # Clean up any existing containers for this project
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=compose_dir,
            capture_output=True
        )
        
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            cwd=compose_dir,
            check=True
        )
        
        console.print("\n[info]Waiting for Tasker API to be ready to push configuration...[/info]")
        import time
        import httpx
        
        api_url = "http://localhost:8888"
        api_ready = False
        for _ in range(30):
            try:
                response = httpx.get(f"{api_url}/health", timeout=2.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("neo4j") == "connected":
                        api_ready = True
                        break
            except Exception:
                pass
            time.sleep(2)
            
        if api_ready:
            console.print("[info]API is ready, configuring project and policies...[/info]")
            
            try:
                # Create project node
                project_data = {
                    "name": project_name,
                    "slug": slug,
                    "description": description,
                    "repositoryUrl": github_repo,
                    "basePackage": base_package,
                    "visibility": visibility,
                    "status": status,
                    "techStack": tech_stack,
                    "mainStack": main_stack,
                    "architectureStyle": architecture,
                    "version": version,
                    "conventionsUrl": conventions_url,
                    "conventionsRules": conventions_rules,
                    "globalStatus": global_status,
                }
                res = httpx.post(f"{api_url}/api/v1/projects", json=project_data, timeout=5.0)
                project_node_id = None
                if res.status_code in (200, 201):
                    console.print("[success]Project node created successfully![/success]")
                    try:
                        project_node_id = res.json().get("data", {}).get("id")
                    except Exception:
                        pass
                        
                    if project_node_id:
                        try:
                            user_data = {
                                "username": username,
                                "email": email,
                                "role": user_role,
                                "github_handle": github_handle,
                            }
                            res_user = httpx.post(f"{api_url}/api/v1/users?project_id={project_node_id}", json=user_data, timeout=5.0)
                            if res_user.status_code in (200, 201):
                                console.print("[success]User node created and linked to project successfully![/success]")
                            else:
                                console.print(f"[warning]Failed to create user node: {res_user.text}[/warning]")
                        except Exception as e:
                            console.print(f"[warning]Failed to create user node: {e}[/warning]")
                else:
                    console.print(f"[warning]Failed to create project node: {res.text}[/warning]")
            except Exception as e:
                console.print(f"[warning]Failed to create project node: {e}[/warning]")
                
            try:
                httpx.post(
                    f"{api_url}/api/v1/components",
                    json={
                        "name": "core",
                        "project": project_name,
                        "description": f"Core component for {project_name}",
                        "labels": ["core", "default", "architecture"]
                    },
                    timeout=5.0
                )
            except Exception as e:
                console.print(f"[warning]Failed to create default component: {e}[/warning]")
                
            policies = [
                {
                    "name": "Forbidden Technologies",
                    "description": forbidden_tech,
                    "target_scope": "PROJECT",
                    "is_active": True,
                    "project_id": project_node_id,
                    "severity": "WARNING"
                },
                {
                    "name": "Required Patterns",
                    "description": required_patterns,
                    "target_scope": "PROJECT",
                    "is_active": True,
                    "project_id": project_node_id,
                    "severity": "WARNING"
                },
                {
                    "name": "Naming Conventions",
                    "description": naming_conventions,
                    "target_scope": "PROJECT",
                    "is_active": True,
                    "project_id": project_node_id,
                    "severity": "WARNING"
                },
                {
                    "name": "Dependency Rules",
                    "description": dependency_rules,
                    "target_scope": "PROJECT",
                    "is_active": True,
                    "project_id": project_node_id,
                    "severity": "WARNING"
                },
                {
                    "name": "Dos and Donts",
                    "description": dos_and_donts,
                    "target_scope": "PROJECT",
                    "is_active": True,
                    "project_id": project_node_id,
                    "severity": "WARNING"
                }
            ]
            
            for policy in policies:
                try:
                    # check if exists
                    existing_res = httpx.get(f"{api_url}/api/v1/policies", params={"name": policy["name"]}, timeout=5.0)
                    exists = False
                    if existing_res.status_code == 200:
                        data = existing_res.json().get("data", {})
                        items = data.get("items", []) if isinstance(data, dict) and "items" in data else (data if isinstance(data, list) else [])
                        for item in items:
                            if item.get("name") == policy["name"]:
                                exists = True
                                break
                    
                    if not exists:
                        res = httpx.post(f"{api_url}/api/v1/policies", json=policy, timeout=5.0)
                        if res.status_code not in (200, 201):
                            console.print(f"[warning]Failed to create policy {policy['name']}: {res.text}[/warning]")
                except Exception as e:
                    console.print(f"[warning]Failed to create policy {policy['name']}: {e}[/warning]")
                    
            console.print("\n[bold green]🎉 TASKER is successfully started and ready![/bold green]")
            console.print("[bold green]You can now focus on writing code. Tasker will handle the rest.[/bold green]")
        else:
            console.print("\n[warning]Tasker started but API did not become ready in time. Policies were not pushed automatically.[/warning]")
            
    except Exception as e:
        console.print(f"\n[bold red]Failed to start Docker Compose: {e}[/bold red]")
        console.print("Please check your Docker installation and try running 'docker compose up -d' manually.")


@init_app.command(name="install")
def install_proxy_command(
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
        help="Initialize in current directory without creating .agent/ subdirectory",
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
    """Scaffold Tasker infrastructure into a project. (Non-interactive)"""
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
    forbidden_tech: str | None = None,
    required_patterns: str | None = None,
    naming_conventions: str | None = None,
    dependency_rules: str | None = None,
    dos_and_donts: str | None = None,
    interactive: bool = False,
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
        output_path = target_path / ".agent"
        if output_path.exists() and not force:
            console.print(f"[warning].agent directory already exists at: {output_path}[/warning]")
            console.print("Use [bold]--force[/bold] to overwrite existing templates.")
            if not interactive:
                raise typer.Exit(code=0)
            return

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

    if project_name or architecture or language or framework or database or github_repo or forbidden_tech or required_patterns or naming_conventions or dependency_rules or dos_and_donts:
        _fill_project_context(
            target_path,
            target_path if inplace else target_path / ".agent",
            project_name,
            architecture,
            language,
            framework,
            database,
            github_repo,
            forbidden_tech,
            required_patterns,
            naming_conventions,
            dependency_rules,
            dos_and_donts,
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

        if not interactive:
            console.print()
            console.print(
                Panel(
                    "[bold]Next steps:[/bold]\n"
                    "  1. cd .agent && cp configs/.env.example configs/.env\n"
                    "  2. Edit .agent/configs/.env and add your OPENAI_API_KEY for RAG features\n"
                    "  3. docker compose build tasker-api\n"
                    "  4. docker compose up -d\n"
                    "  5. Look at .agent/README.md for Agent Workflows and Skills\n"
                    "\n[dim]Note: RAG semantic search requires OPENAI_API_KEY in .env[/dim]",
                    title="[cyan]Tasker & Agent Setup[/cyan]",
                    border_style="cyan",
                )
            )
    else:
        console.print(f"[error]Scaffold completed with {result.error_count} error(s).[/error]")
        raise typer.Exit(code=1) from None


def _fill_project_context(
    target_root: Path,
    tasker_dir: Path,
    project_name: str | None,
    architecture: str | None,
    language: str | None,
    framework: str | None,
    database: str | None,
    github_repo: str | None,
    forbidden_tech: str | None = None,
    required_patterns: str | None = None,
    naming_conventions: str | None = None,
    dependency_rules: str | None = None,
    dos_and_donts: str | None = None,
) -> None:
    """Fill project templates with user-provided values."""
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
        "{k_forbidden_technologies}": forbidden_tech or "- None",
        "{k_required_patterns}": required_patterns or "- Issues must have acceptance criteria",
        "{k_naming_conventions}": naming_conventions or "kebab-case for files, CamelCase for classes",
        "{k_dependency_rules}": dependency_rules or "- Max 10 direct dependencies per issue",
        "{setup_commands}": "pip install -r requirements.txt",
        "{test_commands}": "pytest tests/",
        "{build_commands}": "docker build .",
        "{code_review_count}": "1",
        "{agent_notes}": "- Read .agent/project.md before starting work",
        "{k_dos_and_donts}": dos_and_donts or "- DO: Use .agent/skills/issue_quality_guide.json\n- DON'T: Create vague issues",
    }

    # Markdown files
    md_files = [
        target_root / "README.md",
        target_root / "ROADMAP.md",
        target_root / "VERSIONS.md",
        tasker_dir / "project.md",
        tasker_dir / "AGENT_GUIDE.md",
        tasker_dir / "README.md",
    ]

    for md_file in md_files:
        if md_file.exists():
            content = md_file.read_text(encoding="utf-8")
            for key, value in replacements.items():
                content = content.replace(key, value)
            md_file.write_text(content, encoding="utf-8")
            console.print(f"  [success]Updated:[/success]    {md_file.relative_to(target_root.parent if target_root.parent.exists() else target_root)}")

    # JSON project file (needs different key_components format)
    project_json = tasker_dir / "project.json"
    if project_json.exists():
        json_replacements = replacements.copy()
        json_replacements["{key_components}"] = '"API Gateway", "Backend Service", "Database"'
        
        content = project_json.read_text(encoding="utf-8")
        for key, value in json_replacements.items():
            content = content.replace(key, value)
        project_json.write_text(content, encoding="utf-8")
        console.print(f"  [success]Updated:[/success]    {project_json.relative_to(target_root.parent if target_root.parent.exists() else target_root)}")
