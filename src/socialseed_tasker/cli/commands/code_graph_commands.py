from __future__ import annotations

from contextlib import suppress

import typer
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.cli.commands.shared import console, get_repository

code_graph_app = typer.Typer(help="Code-as-Graph: scan and analyze source code")


@code_graph_app.command("scan")
def code_graph_scan(
    path: str = typer.Argument(..., help="Path to repository to scan"),
    incremental: bool = typer.Option(False, "--incremental", "-i", help="Only scan changed files"),
    git_aware: bool = typer.Option(True, "--git/--no-git", help="Use git to track changes"),
) -> None:
    """Scan a repository and extract code structure into the graph."""
    from socialseed_tasker.infrastructure.code_parser import CodeGraphParser
    from socialseed_tasker.application.wiring import get_driver

    console.print(f"[info]Scanning repository:[/info] {path}")

    parser = CodeGraphParser()

    try:
        files, symbols, imports, relationships = parser.scan_repository(
            repository_path=path,
            incremental=incremental,
            git_aware=git_aware,
        )

        console.print(f"[success]Found {len(files)} files, {len(symbols)} symbols, {len(imports)} imports[/success]")

        driver = get_driver()
        if driver:
            from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

            repo = CodeGraphRepository(driver)
            repo.save_scan_results(files, symbols, imports, relationships)
            console.print("[success]Saved to Neo4j graph[/success]")
        else:
            console.print("[warning]Neo4j not connected - results not saved[/warning]")

    except Exception as e:
        console.print(f"[error]Error scanning repository:[/error] {str(e)}")


@code_graph_app.command("find")
def code_graph_find(
    name: str = typer.Argument(..., help="Symbol name to search for"),
    symbol_type: str | None = typer.Option(None, "--type", "-t", help="Filter by symbol type"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
) -> None:
    """Find symbols by name in the code graph."""
    from socialseed_tasker.domain.code_analysis_entities import SymbolType
    from socialseed_tasker.application.wiring import get_driver

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)

    sym_type = None
    if symbol_type:
        with suppress(ValueError):
            sym_type = SymbolType(symbol_type)

    results = repo.find_symbols(name=name, symbolType=sym_type, limit=limit)

    if not results:
        console.print("[info]No symbols found[/info]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", width=30)
    table.add_column("Type", width=15)
    table.add_column("File", width=30)
    table.add_column("Line", width=8)

    for sym in results:
        table.add_row(
            sym.get("name", ""),
            sym.get("symbolType", ""),
            sym.get("filePath", ""),
            str(sym.get("startLine", "")),
        )

    console.print(Panel(table, title=f"[bold]Symbols ({len(results)} found)[/bold]"))


@code_graph_app.command("files")
def code_graph_files(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results"),
    language: str | None = typer.Option(None, "--language", help="Filter by language"),
) -> None:
    """List files in the code graph."""
    from socialseed_tasker.application.wiring import get_driver

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)
    files = repo.get_files(limit=limit)

    if not files:
        console.print("[info]No files in graph[/info]")
        return

    if language:
        files = [f for f in files if f.get("language") == language]

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Path", width=50)
    table.add_column("Name", width=30)
    table.add_column("Language", width=15)
    table.add_column("Lines", width=8)

    for f in files:
        table.add_row(
            f.get("path", ""),
            f.get("name", ""),
            f.get("language", ""),
            str(f.get("linesOfCode", 0)),
        )

    console.print(Panel(table, title=f"[bold]Files ({len(files)} found)[/bold]"))


@code_graph_app.command("stats")
def code_graph_stats() -> None:
    """Show code graph statistics."""
    from socialseed_tasker.application.wiring import get_driver

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)
    stats = repo.get_stats()

    console.print(Panel(
        f"[bold]Total Files:[/bold] {stats.totalFiles}\n"
        f"[bold]Total Symbols:[/bold] {stats.totalSymbols}\n"
        f"[bold]Total Relationships:[/bold] {stats.totalRelationships}",
        title="[bold]Code Graph Statistics[/bold]",
    ))


@code_graph_app.command("clear")
def code_graph_clear(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion"),
) -> None:
    """Clear all code graph data from Neo4j."""
    from socialseed_tasker.application.wiring import get_driver

    if not confirm:
        console.print("[warning]Use --yes to confirm deletion[/warning]")
        return

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    repo = CodeGraphRepository(driver)
    repo.clear()
    console.print("[success]Code graph cleared[/success]")


@code_graph_app.command("impact")
def code_graph_impact(
    symbol_name: str = typer.Argument(..., help="Symbol name to analyze impact for"),
) -> None:
    """Analyze the impact of changing a symbol (find all callers)."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = CodeGraphRepository(driver)
    callers = repo.get_callers(symbol_name)

    if not callers:
        console.print(f"[info]No direct callers found for symbol '{symbol_name}'[/info]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Caller Symbol", width=30)
    table.add_column("Type", width=15)
    table.add_column("File ID", width=40)

    for caller in callers:
        table.add_row(
            caller.get("name", ""),
            caller.get("symbolType", ""),
            caller.get("fileId", ""),
        )

    console.print(Panel(table, title=f"[bold]Impact Analysis for '{symbol_name}'[/bold]"))


@code_graph_app.command("calls")
def code_graph_calls(
    path: str = typer.Argument(..., help="File or symbol path"),
) -> None:
    """Find all functions that call a specific function/method."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = CodeGraphRepository(driver)
    callers = repo.get_callers_by_path(path)

    if not callers:
        console.print(f"[info]No callers found for '{path}'[/info]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Caller", width=30)
    table.add_column("Type", width=15)
    table.add_column("File", width=30)

    for caller in callers:
        table.add_row(
            caller.get("name", ""),
            caller.get("symbolType", ""),
            caller.get("filePath", ""),
        )

    console.print(Panel(table, title=f"[bold]Callers of '{path}'[/bold]"))


@code_graph_app.command("depends")
def code_graph_depends(
    path: str = typer.Argument(..., help="File or symbol path"),
) -> None:
    """Find dependencies (imports) for a file."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = CodeGraphRepository(driver)
    deps = repo.get_dependencies_by_path(path)

    if not deps:
        console.print(f"[info]No dependencies found for '{path}'[/info]")
        return

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Module", width=40)
    table.add_column("Line", width=8)
    table.add_column("Type", width=10)

    for dep in deps:
        table.add_row(
            dep.get("module", ""),
            str(dep.get("line_number", "-")),
            "from" if dep.get("is_from") else "import",
        )

    console.print(Panel(table, title=f"[bold]Dependencies of '{path}'[/bold]"))


@code_graph_app.command("tests")
def code_graph_tests(
    path: str = typer.Argument(..., help="Source file path"),
) -> None:
    """Find test files related to a source file."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = CodeGraphRepository(driver)
    tests = repo.get_tests_for_file(path)

    if not tests:
        console.print(f"[info]No test files found for '{path}'[/info]")
        return

    table = Table(show_header=True, header_style="bold green")
    table.add_column("Test File", width=50)
    table.add_column("Type", width=15)

    for test in tests:
        table.add_row(
            test.get("path", ""),
            test.get("symbolType", ""),
        )

    console.print(Panel(table, title=f"[bold]Tests for '{path}'[/bold]"))


@code_graph_app.command("file")
def code_graph_file(
    path: str = typer.Argument(..., help="File path to show details"),
) -> None:
    """Show detailed information about a file in the graph."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = CodeGraphRepository(driver)
    file_data = repo.get_file_by_path(path, "")

    if not file_data:
        console.print(f"[error]File not found in graph: {path}[/error]")
        return

    console.print(Panel(
        f"[bold]File:[/bold] {file_data.get('name', path)}\n"
        f"[bold]Path:[/bold] {file_data.get('path', 'N/A')}\n"
        f"[bold]Language:[/bold] {file_data.get('language', 'N/A')}\n"
        f"[bold]Lines:[/bold] {file_data.get('lines_of_code', 0)}\n"
        f"[bold]Hash:[/bold] {file_data.get('file_hash', 'N/A')[:16]}...",
        title=f"[bold]File Details[/bold]",
    ))
