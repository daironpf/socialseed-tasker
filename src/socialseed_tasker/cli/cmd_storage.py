"""Storage management commands.

Enables schema migrations and data maintenance for Neo4j.
"""

from __future__ import annotations

import typer
from rich.console import Console

from socialseed_tasker.storage.graph_database.migrations.v090 import run_migration, rollback_migration

console = Console()
storage_app = typer.Typer(help="Manage Neo4j storage and schema")

@storage_app.command("migrate")
def storage_migrate(
    version: str = typer.Option("0.9.0", "--version", "-v", help="Migration version"),
) -> None:
    """Run Neo4j schema migrations."""
    from socialseed_tasker.entrypoints.terminal_cli.commands import get_repository
    from socialseed_tasker.storage.graph_database.repositories import Neo4jTaskRepository
    
    repo = get_repository()
    if not isinstance(repo, Neo4jTaskRepository):
        console.print("[error]Storage migration is only supported for Neo4j backend.[/error]")
        raise typer.Exit(1)
        
    driver = repo._driver
    
    if version == "0.9.0":
        success = run_migration(driver)
        if success:
            console.print("[success]Migration v0.9.0 completed successfully.[/success]")
        else:
            console.print("[error]Migration v0.9.0 failed.[/error]")
            raise typer.Exit(1)
    else:
        console.print(f"[error]Unknown migration version: {version}[/error]")
        raise typer.Exit(1)

@storage_app.command("rollback")
def storage_rollback(
    version: str = typer.Option("0.9.0", "--version", "-v", help="Migration version"),
) -> None:
    """Roll back Neo4j schema migrations."""
    from socialseed_tasker.entrypoints.terminal_cli.commands import get_repository
    from socialseed_tasker.storage.graph_database.repositories import Neo4jTaskRepository
    
    repo = get_repository()
    if not isinstance(repo, Neo4jTaskRepository):
        console.print("[error]Storage rollback is only supported for Neo4j backend.[/error]")
        raise typer.Exit(1)
        
    driver = repo._driver
    
    if version == "0.9.0":
        success = rollback_migration(driver)
        if success:
            console.print("[success]Rollback v0.9.0 completed successfully.[/success]")
        else:
            console.print("[error]Rollback v0.9.0 failed.[/error]")
            raise typer.Exit(1)
    else:
        console.print(f"[error]Unknown rollback version: {version}[/error]")
        raise typer.Exit(1)
