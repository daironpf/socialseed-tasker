"""Project detection commands for structure analysis and module creation."""

from __future__ import annotations

import json
from contextlib import suppress
from pathlib import Path
from typing import Any

import typer
from rich.box import SIMPLE
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.cli.commands.shared import (
    console,
    get_repository,
)

# ---------------------------------------------------------------------------
# Project app (create, detect, setup)
# ---------------------------------------------------------------------------

project_app = typer.Typer(help="Manage projects in the Tasker system")


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
        console.print(f"[error]Path does not exist: {project_path.as_posix()}[/error]")
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


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name"),
    slug: str = typer.Option(None, "--slug", "-s", help="URL-friendly slug (defaults to name)"),
    description: str = typer.Option("", "--description", "-d", help="Project description"),
    visibility: str = typer.Option("PUBLIC", "--visibility", "-v", help="Project visibility (PUBLIC, PRIVATE)"),
    status: str = typer.Option("DEVELOPMENT", "--status", help="Project status"),
) -> None:
    """Create a new project in Tasker.

    Tasker supports only ONE project. If one already exists,
    this command returns the existing project instead.
    """
    repo = get_repository()

    existing = repo.list_projects()
    if existing:
        proj_name = existing[0]
        console.print(f"[warning]A project already exists:[/warning] '{proj_name}'.")
        console.print("[info]Tasker supports only ONE project per instance.[/info]")
        return

    if not slug:
        slug = name.lower().replace(" ", "-")

    project_data: dict[str, Any] = {
        "name": name,
        "slug": slug,
        "description": description,
        "visibility": visibility,
        "status": status,
    }

    result = repo.create_project(project_data)
    if result.get("status") == "exists":
        proj = result.get("project", {})
        console.print(f"[warning]Project already exists:[/warning] {proj.get('name', name)} (id: {proj.get('id', '?')})")
    else:
        project_id = result.get("id", "?")
        console.print(f"[success]Project created:[/success] {name} (id: {project_id})")


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
        console.print(f"[error]Path does not exist: {project_path.as_posix()}[/error]")
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
            from socialseed_tasker.domain.entities import Component

            component = Component(name=module["name"], description=module["description"], project=proj_name)
            component = repo.create_component(component)
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


__all__ = ["project_app"]
