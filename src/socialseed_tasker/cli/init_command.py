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
import sys

import socialseed_tasker

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from socialseed_tasker.domain.system_init_entities import FileOperation, ScaffoldStatus
from socialseed_tasker.application.scaffolder import ScaffolderService


def _ask(
    prompt: str,
    default: str | None = None,
    password: bool = False,
    choices: list[str] | None = None,
) -> str:
    """Prompt the user, falling back to input() when stdin is not a TTY."""
    try:
        return Prompt.ask(prompt, default=default, password=password, choices=choices)
    except (EOFError, KeyboardInterrupt):
        if default is not None:
            return default
        return input(f"{prompt} ")


def _confirm(prompt: str, default: bool = False) -> bool:
    """Confirm prompt, falling back to default when stdin is not a TTY."""
    try:
        return typer.confirm(prompt, default=default)
    except (EOFError, KeyboardInterrupt):
        return default

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
    return Path(__file__).parent.parent / "assets" / "templates"


def _get_frontend_dir() -> Path:
    """Return the path to the bundled frontend build assets."""
    return Path(__file__).parent.parent / "assets" / "frontend"


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
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip interactive prompts and use all default values",
    ),
) -> None:
    """Initialize Tasker in a project interactively.

    Prompts for project details before scaffolding.
    Use --yes to skip all prompts and accept defaults (useful for scripting/CI).
    """
    console.print("[bold cyan]Welcome to SocialSeed Tasker Initialization[/bold cyan]")
    console.print("Configure your project using the menu below.\n")
    
    # Initialize defaults
    project_name = "my-project"
    architecture = "api-first"
    language = "python"
    framework = "fastapi"
    database = "postgresql"
    github_repo = "https://github.com/user/repo"
    slug = "my-project"
    description = "Tasker project for my-project"
    base_package = "my_project"
    visibility = "PUBLIC"
    status = "DEVELOPMENT"
    tech_stack_str = "python, fastapi, postgresql"
    main_stack_str = "python, Neo4j"
    version = "0.1.0"
    conventions_url = ""
    conventions_rules = "- Use standard conventions"
    global_status = "DEVELOPMENT"
    
    username = "admin"
    email = "admin@example.com"
    user_role = "ADMIN"
    github_handle = "admin"
    
    forbidden_tech = "- None"
    required_patterns = "- Issues must have acceptance criteria"
    naming_conventions = "kebab-case for files, CamelCase for classes"
    dependency_rules = "- Max 10 direct dependencies per issue"
    dos_and_donts = "- DO: Use .agent/skills/issue_quality_guide.json\n- DON'T: Create vague issues"
    
    # New fields
    agent_name = "Architect-Agent"
    agent_role = "planner"
    agent_capabilities = "coding,testing,architecture"
    openai_api_key = ""
    components_list_str = "core"
    
    state = {
        "1": False, # Project Identity
        "2": False, # Tech Stack
        "3": False, # Project Settings
        "4": False, # User Config
        "5": False, # Policies
        "6": False, # Agent Config
        "7": False, # API Keys
        "8": False, # Components
    }
    
    if yes:
        console.print("[dim]--yes flag detected, using all default values.[/dim]")
    else:
        while True:
            table = Table(title="[bold cyan]Tasker Setup Menu[/bold cyan]", box=None)
            table.add_column("Option", justify="right", style="cyan")
            table.add_column("Category", style="white")
            table.add_column("Status", style="yellow")
            
            table.add_row("1", "Project Identity", "[green]Filled[/green]" if state["1"] else "[red]Pending (Defaults will be used)[/red]")
            table.add_row("2", "Tech Stack", "[green]Filled[/green]" if state["2"] else "[red]Pending[/red]")
            table.add_row("3", "Project Settings", "[green]Filled[/green]" if state["3"] else "[red]Pending[/red]")
            table.add_row("4", "User Config (Human)", "[green]Filled[/green]" if state["4"] else "[red]Pending[/red]")
            table.add_row("5", "Policies & Constraints", "[green]Filled[/green]" if state["5"] else "[red]Pending[/red]")
            table.add_row("6", "Agent Config", "[green]Filled[/green]" if state["6"] else "[red]Pending[/red]")
            table.add_row("7", "API Keys (OpenAI)", "[green]Filled[/green]" if state["7"] else "[red]Pending[/red]")
            table.add_row("8", "Initial Components", "[green]Filled[/green]" if state["8"] else "[red]Pending[/red]")
            table.add_row("", "", "")
            table.add_row("START", "[bold green]Run Setup[/bold green]", "")
            table.add_row("EXIT", "[bold red]Cancel[/bold red]", "")
            
            console.print(table)
            
            choice = _ask("Select an option", default="START").upper()
            
            if choice == "EXIT":
                console.print("[yellow]Initialization cancelled.[/yellow]")
                raise typer.Exit(code=0)
                
            elif choice == "START":
                # If nothing filled, ask for project name
                if not any(state.values()) or not state["1"]:
                    project_name = _ask("Project Name required to proceed", default=project_name)
                    slug = project_name.lower().replace(" ", "-")
                    description = f"Tasker project for {project_name}"
                    base_package = project_name.lower().replace(" ", "_")
                    state["1"] = True
                break
                
            elif choice == "1":
                project_name = _ask("Project Name", default=project_name)
                github_repo = _ask("GitHub Repository URL", default=github_repo)
                slug = _ask("Project Slug", default=project_name.lower().replace(" ", "-"))
                description = _ask("Project Description", default=f"Tasker project for {project_name}")
                # Update base_package default if not filled yet
                if not state["3"]:
                    base_package = project_name.lower().replace(" ", "_")
                state["1"] = True
                
            elif choice == "2":
                architecture = _ask("Architecture", default=architecture)
                language = _ask("Primary Language", default=language)
                framework = _ask("Framework", default=framework)
                database = _ask("Database", default=database)
                tech_stack_str = _ask("Tech Stack (comma separated)", default=f"{language}, {framework}, {database}")
                main_stack_str = _ask("Main Stack (comma separated)", default=f"{language}, Neo4j")
                state["2"] = True
                
            elif choice == "3":
                base_package = _ask("Base Package", default=base_package)
                visibility = _ask("Visibility", choices=["PUBLIC", "PRIVATE"], default=visibility)
                status = _ask("Project Status", default=status)
                version = _ask("Version", default=version)
                conventions_url = _ask("Conventions URL", default=conventions_url)
                conventions_rules = _ask("Conventions Rules", default=conventions_rules)
                global_status = _ask("Global Status", choices=["DEVELOPMENT", "STAGING", "PRODUCTION"], default=global_status)
                state["3"] = True
                
            elif choice == "4":
                username = _ask("Username", default=username)
                email = _ask("Email", default=email)
                user_role = _ask("Role", choices=["ADMIN", "LEAD_ARCHITECT", "DEVELOPER"], default=user_role)
                github_handle = _ask("GitHub Handle", default=github_handle)
                state["4"] = True
                
            elif choice == "5":
                forbidden_tech = _ask("Forbidden Technologies", default=forbidden_tech)
                required_patterns = _ask("Required Patterns", default=required_patterns)
                naming_conventions = _ask("Naming Conventions", default=naming_conventions)
                dependency_rules = _ask("Dependency Rules", default=dependency_rules)
                dos_and_donts = _ask("Do's and Don'ts", default=dos_and_donts)
                state["5"] = True
                
            elif choice == "6":
                agent_name = _ask("Agent Name", default=agent_name)
                agent_role = _ask("Agent Role", default=agent_role)
                agent_capabilities = _ask("Agent Capabilities (comma separated)", default=agent_capabilities)
                state["6"] = True
                
            elif choice == "7":
                openai_api_key = _ask("OpenAI API Key (hidden)", password=True)
                state["7"] = True
                
            elif choice == "8":
                components_list_str = _ask("Initial Components (comma separated)", default=components_list_str)
                state["8"] = True
                
            else:
                console.print("[red]Invalid option.[/red]")
                
            console.print("\n" + "="*40 + "\n")

    # Mode selection
    cli_mode = "direct"
    if not yes:
        console.print("\n[bold cyan]Connection Mode[/bold cyan]")
        console.print("Choose how the CLI connects to the backend:")
        console.print("  [bold]1) Direct (Neo4j Bolt)[/bold] - CLI connects directly to Neo4j via Bolt protocol")
        console.print("  [bold]2) API (REST)[/bold] - CLI connects through the FastAPI REST API")
        console.print("")
        mode_choice = _ask("Select mode", choices=["1", "2"], default="1")
        cli_mode = "direct" if mode_choice == "1" else "api"

    console.print("\n[info]Starting initialization with provided context...[/info]\n")
    
    tech_stack = [s.strip() for s in tech_stack_str.split(",") if s.strip()]
    main_stack = [s.strip() for s in main_stack_str.split(",") if s.strip()]
    components_list = [s.strip() for s in components_list_str.split(",") if s.strip()]
    
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

    # Write mode configuration
    _write_mode_config(target, inplace, cli_mode)

    # Handle API keys in .env
    if openai_api_key:
        try:
            env_path = Path(target) / (".agent/configs/.env" if not inplace else "configs/.env")
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                content = content.replace("OPENAI_API_KEY=", f"OPENAI_API_KEY={openai_api_key}")
                env_path.write_text(content, encoding="utf-8")
                console.print("[success]Updated .env with OpenAI API Key.[/success]")
        except Exception as e:
            console.print(f"[warning]Failed to update .env: {e}[/warning]")

    console.print("\n[info]Starting Tasker infrastructure via Docker Compose...[/info]")
    try:
        compose_dir = Path(target).resolve()
        if not inplace:
            compose_dir = compose_dir / ".agent" / "tasker"
            
        # Clean up any existing containers for this project
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=compose_dir,
            capture_output=True,
        )
        
        # Build a wheel of the current package for the Docker image.
        # The wheel is placed in the build context directory (.agent/dist/)
        # so the Dockerfile can COPY it.
        if cli_mode != "direct":
            build_context_dir = compose_dir.parent if not inplace else compose_dir
            dist_dir = build_context_dir / "dist"
            dist_dir.mkdir(parents=True, exist_ok=True)
            console.print("[info]Building package wheel for Docker image...[/info]")
            pkg_init = Path(socialseed_tasker.__file__).resolve()
            project_root = next(
                (p for p in pkg_init.parents if (p / "pyproject.toml").exists()),
                pkg_init.parent.parent,
            )
            wheel_result = subprocess.run(
                [sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(dist_dir), str(project_root)],
                capture_output=True,
                text=True,
            )
            if wheel_result.returncode != 0:
                console.print(f"[warning]Failed to build wheel: {wheel_result.stderr.strip()}[/warning]")
                console.print("[warning]Falling back to PyPI install for API container.[/warning]")
            else:
                wheels = [f.name for f in dist_dir.glob("*.whl")]
                if wheels:
                    console.print(f"[success]Wheel built: {wheels[0]}[/success]")
        
        compose_profile = [] if cli_mode == "direct" else ["--profile", "api"]
        subprocess.run(
            ["docker", "compose", *compose_profile, "up", "-d", "--build"],
            cwd=compose_dir,
            check=True,
        )
        
        if cli_mode == "direct":
            console.print("\n[info]Tasker initialized in Direct mode. Neo4j is running and ready.[/info]")
            console.print("[bold green]SUCCESS: TASKER is successfully started and ready![/bold green]")
            console.print("[bold green]You can now use 'tasker' commands to manage your project.[/bold green]")
            return

        console.print("\n[info]Waiting for Tasker API to be ready to push configuration...[/info]")
        import time
        import httpx
        
        api_url = "http://localhost:8888"
        api_ready = False
        for _ in range(60):
            try:
                response = httpx.get(f"{api_url}/health", timeout=2.0)
                if response.status_code == 200:
                    api_ready = True
                    break
            except Exception:
                pass
            time.sleep(2)

        if api_ready:
            time.sleep(3)  # allow API to finalize initialization after health check
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

                    # Create Agent node only if user filled agent config
                    if state.get("6") and agent_name and agent_name != "Architect-Agent":
                        try:
                            agent_id_to_use = agent_name.lower().replace(" ", "-")
                            agent_data = {
                                "agent_id": agent_id_to_use,
                                "name": agent_name,
                                "role": agent_role,
                                "capabilities": [c.strip() for c in agent_capabilities.split(",") if c.strip()],
                                "status": "IDLE"
                            }
                            res_agent = httpx.post(f"{api_url}/api/v1/agents/register", json=agent_data, timeout=5.0)
                            if res_agent.status_code in (200, 201):
                                console.print("[success]Agent node created successfully![/success]")
                                try:
                                    agent_id = res_agent.json().get("data", {}).get("agent_id") or agent_id_to_use
                                    if agent_id:
                                        res_assign = httpx.post(f"{api_url}/api/v1/projects/{project_node_id}/agents/{agent_id}", timeout=5.0)
                                        if res_assign.status_code in (200, 201):
                                            console.print("[success]Agent assigned to project successfully![/success]")
                                except Exception:
                                    pass
                            else:
                                console.print(f"[warning]Failed to create agent node: {res_agent.text}[/warning]")
                        except Exception as e:
                            console.print(f"[warning]Failed to create agent node: {e}[/warning]")
                    else:
                        console.print("[dim]Skipping agent creation (option 6 not filled by user).[/dim]")

            except Exception as e:
                console.print(f"[warning]Failed to create project node: {e}[/warning]")

            # Create components
            created_components = []
            for comp_name in components_list:
                try:
                    res_comp = httpx.post(
                        f"{api_url}/api/v1/components",
                        json={
                            "name": comp_name,
                            "project": project_name,
                            "description": f"{comp_name.capitalize()} component for {project_name}",
                            "labels": [comp_name, "architecture"]
                        },
                        timeout=5.0
                    )
                    if res_comp.status_code in (200, 201):
                        console.print(f"[success]Component '{comp_name}' created successfully![/success]")
                        comp_data = res_comp.json()
                        if isinstance(comp_data, dict) and "data" in comp_data:
                            created_components.append(comp_data["data"].get("id"))
                        else:
                            created_components.append(comp_data.get("id"))
                    else:
                        console.print(f"[warning]Failed to create component '{comp_name}': {res_comp.text}[/warning]")
                except Exception as e:
                    console.print(f"[warning]Failed to create component '{comp_name}': {e}[/warning]")
                    
            # Create first issue if a component exists
            if created_components:
                console.print("[info]Creating first issue for the project...[/info]")
                try:
                    res_issue = httpx.post(
                        f"{api_url}/api/v1/issues",
                        json={
                            "title": f"Explore {project_name} codebase",
                            "description": "Initial task to explore the codebase and identify key components.",
                            "priority": "MEDIUM",
                            "component_id": created_components[0],
                            "labels": ["initial", "setup"]
                        },
                        timeout=5.0
                    )
                    if res_issue.status_code in (200, 201):
                        console.print("[success]First issue created successfully![/success]")
                    else:
                        console.print(f"[warning]Failed to create first issue: {res_issue.text}[/warning]")
                except Exception as e:
                    console.print(f"[warning]Failed to create first issue: {e}[/warning]")
                    
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
                    
            console.print("\n[bold green]SUCCESS: TASKER is successfully started and ready![/bold green]")
            console.print("[bold green]You can now focus on writing code. Tasker will handle the rest.[/bold green]")
        else:
            console.print("\n[warning]Tasker started but API did not become ready in time. Policies were not pushed automatically.[/warning]")
            
    except Exception as e:
        console.print(f"\n[bold red]Failed to start Docker Compose: {e}[/bold red]")
        console.print("Please check your Docker installation and try running 'docker compose up -d' manually.")
        raise typer.Exit(code=1)


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
        existing_project_file = target_path / ".agent" / "tasker" / "project.json"
        if output_path.exists():
            if existing_project_file.exists() and force:
                console.print(
                    f"[warning]Existing Tasker project detected at: {target_path}[/warning]"
                )
                console.print(
                    "[warning]Using --force will overwrite current project configuration "
                    "(.agent/tasker/ files, ROADMAP.md, VERSIONS.md).[/warning]"
                )
                if interactive:
                    confirm = _confirm("Continue overwriting?", default=False)
                    if not confirm:
                        console.print("[info]Scaffold cancelled.[/info]")
                        raise typer.Exit(code=0)
            elif not force:
                console.print(f"[warning].agent directory already exists at: {output_path}[/warning]")
                console.print("Use [bold]--force[/bold] to overwrite existing templates.")
                if not interactive:
                    raise typer.Exit(code=0)
                # Still apply placeholder replacement even when scaffold is skipped
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
        "{database}": database or "neo4j",
        "{frontend}": "vue",
        "{other_services}": "tree-sitter, openai",
        "{key_components}": "- Task Management\n- Code Analysis\n- Agent Coordination",
        "{github_repo}": github_repo or "",
        "{default_branch}": "main",
        "{external_apis}": "- None configured",
        "{k_forbidden_technologies}": forbidden_tech or "- Neo4j-only storage\n- No file storage",
        "{k_required_patterns}": required_patterns or "- Hexagonal Architecture\n- Repository Pattern",
        "{k_naming_conventions}": naming_conventions or "snake_case functions, PascalCase classes",
        "{k_dependency_rules}": dependency_rules or "- Max 5 dependency depth",
        "{setup_commands}": "pip install -e . && docker compose up -d",
        "{test_commands}": "pytest tests/",
        "{build_commands}": "pip install -e . && pip wheel . --wheel-dir dist/",
        "{code_review_count}": "1",
        "{agent_notes}": "- Read .agent/project.md before starting work\n- Use .agent/AGENT_GUIDE.md for protocol\n- Consult Tasker first for all project-related requests",
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


def _write_mode_config(target: str, inplace: bool, mode: str) -> None:
    """Write .agent/configs/tasker.yml with the chosen CLI mode."""
    config_dir = Path(target).resolve()
    if not inplace:
        config_dir = config_dir / ".agent" / "configs"
    else:
        config_dir = config_dir / "configs"

    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "tasker.yml"

    content = f"""# Tasker CLI mode configuration
# Generated by `tasker init`
mode: {mode}
api_url: http://localhost:8888
# api_key: your-api-key-here
neo4j_uri: bolt://localhost:7687
neo4j_user: neo4j
neo4j_password: neoSocial
"""
    config_file.write_text(content, encoding="utf-8")
    console.print(f"  [success]Created:[/success]    {config_file.relative_to(Path(target).resolve())}")
