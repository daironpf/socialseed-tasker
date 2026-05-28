from __future__ import annotations

from contextlib import suppress
from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.cli.commands.shared import console
from socialseed_tasker.config.mode_config import DualModeConfig

CG_API = "/api/v1/code-graph"
code_graph_app = typer.Typer(help="Code-as-Graph: scan and analyze source code")


def _get_client() -> Any | None:
    cfg = DualModeConfig.load()
    if cfg.mode == "api":
        from socialseed_tasker.infrastructure.http.api_client import ApiHttpClient
        return ApiHttpClient(base_url=cfg.api_url, api_key=cfg.api_key or None, timeout=cfg.api_timeout)
    return None


def _call_api(client: Any, method: str, path: str, **kwargs) -> Any:
    return client.request(method, path, **kwargs)


@code_graph_app.command("scan")
def code_graph_scan(
    path: str = typer.Argument(..., help="Path to repository to scan"),
    incremental: bool = typer.Option(False, "--incremental", "-i", help="Only scan changed files"),
    git_aware: bool = typer.Option(True, "--git/--no-git", help="Use git to track changes"),
) -> None:
    """Scan a repository and extract code structure into the graph."""
    from socialseed_tasker.infrastructure.code_parser import CodeGraphParser

    console.print(f"[info]Scanning repository:[/info] {path}")
    parser = CodeGraphParser()

    try:
        files, symbols, imports, relationships = parser.scan_repository(
            repository_path=path, incremental=incremental, git_aware=git_aware,
        )
        console.print(f"[success]Found {len(files)} files, {len(symbols)} symbols, {len(imports)} imports[/success]")

        client = _get_client()
        if client:
            result = _call_api(client, "POST", f"{CG_API}/scan", params={
                "path": path, "incremental": incremental, "git_aware": git_aware,
            })
            console.print(f"[success]Saved to graph via API[/success]")
            return

        from socialseed_tasker.application.wiring import get_driver
        driver = get_driver()
        if driver:
            from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
            CodeGraphRepository(driver).save_scan_results(files, symbols, imports, relationships)
            console.print("[success]Saved to Neo4j graph[/success]")
        else:
            console.print("[warning]Neo4j not connected - results not saved[/warning]")

    except Exception as e:
        console.print(f"[error]Error scanning repository:[/error] {str(e)}")
        raise typer.Exit(code=1)


@code_graph_app.command("find")
def code_graph_find(
    name: str = typer.Argument(..., help="Symbol name to search for"),
    symbol_type: str | None = typer.Option(None, "--type", "-t", help="Filter by symbol type"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
) -> None:
    """Find symbols by name in the code graph."""
    client = _get_client()
    if client:
        params: dict[str, Any] = {"name": name, "limit": limit}
        if symbol_type:
            params["symbol_type"] = symbol_type
        result = _call_api(client, "GET", f"{CG_API}/symbols", params=params)
        symbols = result if isinstance(result, list) else result.get("symbols", [])
        if not symbols:
            console.print("[info]No symbols found[/info]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", width=30); table.add_column("Type", width=15)
        table.add_column("File", width=30); table.add_column("Line", width=8)
        for sym in symbols:
            table.add_row(sym.get("name", ""), sym.get("symbolType", sym.get("symbol_type", "")),
                          sym.get("filePath", sym.get("file_path", "")), str(sym.get("startLine", sym.get("start_line", ""))))
        console.print(Panel(table, title=f"[bold]Symbols ({len(symbols)} found)[/bold]"))
        return

    from socialseed_tasker.domain.code_analysis_entities import SymbolType
    from socialseed_tasker.application.wiring import get_driver
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    repo = CodeGraphRepository(driver)
    results = repo.find_symbols(name=name, symbolType=sym_type, limit=limit)
    if not results:
        console.print("[info]No symbols found[/info]")
        return
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", width=30); table.add_column("Type", width=15)
    table.add_column("File", width=30); table.add_column("Line", width=8)
    for sym in results:
        table.add_row(sym.get("name", ""), sym.get("symbolType", ""), sym.get("filePath", ""), str(sym.get("startLine", "")))
    console.print(Panel(table, title=f"[bold]Symbols ({len(results)} found)[/bold]"))


@code_graph_app.command("files")
def code_graph_files(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results"),
    language: str | None = typer.Option(None, "--language", help="Filter by language"),
) -> None:
    """List files in the code graph."""
    client = _get_client()
    if client:
        params: dict[str, Any] = {"limit": limit}
        if language:
            params["language"] = language
        result = _call_api(client, "GET", f"{CG_API}/files", params=params)
        files = result if isinstance(result, list) else result.get("files", [])
        if not files:
            console.print("[info]No files in graph[/info]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Path", width=50); table.add_column("Name", width=30)
        table.add_column("Language", width=15); table.add_column("Lines", width=8)
        for f in files:
            table.add_row(f.get("path", ""), f.get("name", ""), f.get("language", ""), str(f.get("linesOfCode", f.get("lines_of_code", 0))))
        console.print(Panel(table, title=f"[bold]Files ({len(files)} found)[/bold]"))
        return

    from socialseed_tasker.application.wiring import get_driver
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    repo = CodeGraphRepository(driver)
    files = repo.get_files(limit=limit)
    if not files:
        console.print("[info]No files in graph[/info]")
        return
    if language:
        files = [f for f in files if f.get("language") == language]
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Path", width=50); table.add_column("Name", width=30)
    table.add_column("Language", width=15); table.add_column("Lines", width=8)
    for f in files:
        table.add_row(f.get("path", ""), f.get("name", ""), f.get("language", ""), str(f.get("linesOfCode", 0)))
    console.print(Panel(table, title=f"[bold]Files ({len(files)} found)[/bold]"))


@code_graph_app.command("stats")
def code_graph_stats() -> None:
    """Show code graph statistics."""
    client = _get_client()
    if client:
        result = _call_api(client, "GET", f"{CG_API}/stats")
        stats = result if isinstance(result, dict) else {}
        console.print(Panel(
            f"[bold]Total Files:[/bold] {stats.get('total_files', stats.get('totalFiles', 0))}\n"
            f"[bold]Total Symbols:[/bold] {stats.get('total_symbols', stats.get('totalSymbols', 0))}\n"
            f"[bold]Total Relationships:[/bold] {stats.get('total_relationships', stats.get('totalRelationships', 0))}",
            title="[bold]Code Graph Statistics[/bold]",
        ))
        return

    from socialseed_tasker.application.wiring import get_driver
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
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
def code_graph_clear(confirm: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion")) -> None:
    """Clear all code graph data."""
    if not confirm:
        console.print("[warning]Use --yes to confirm deletion[/warning]")
        return
    client = _get_client()
    if client:
        _call_api(client, "DELETE", f"{CG_API}/")
        console.print("[success]Code graph cleared[/success]")
        return
    from socialseed_tasker.application.wiring import get_driver
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    CodeGraphRepository(driver).clear()
    console.print("[success]Code graph cleared[/success]")


@code_graph_app.command("impact")
def code_graph_impact(symbol_name: str = typer.Argument(..., help="Symbol name to analyze impact for")) -> None:
    """Analyze the impact of changing a symbol (find all callers)."""
    client = _get_client()
    if client:
        result = _call_api(client, "GET", f"{CG_API}/calls/{symbol_name}")
        callers = result if isinstance(result, list) else result.get("callers", [])
        if not callers:
            console.print(f"[info]No direct callers found for symbol '{symbol_name}'[/info]")
            return
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Caller Symbol", width=30); table.add_column("Type", width=15); table.add_column("File ID", width=40)
        for caller in callers:
            table.add_row(caller.get("name", ""), caller.get("symbolType", caller.get("symbol_type", "")), caller.get("fileId", caller.get("file_id", "")))
        console.print(Panel(table, title=f"[bold]Impact Analysis for '{symbol_name}'[/bold]"))
        return

    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    repo = CodeGraphRepository(driver)
    callers = repo.get_callers(symbol_name)
    if not callers:
        console.print(f"[info]No direct callers found for symbol '{symbol_name}'[/info]")
        return
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Caller Symbol", width=30); table.add_column("Type", width=15); table.add_column("File ID", width=40)
    for caller in callers:
        table.add_row(caller.get("name", ""), caller.get("symbolType", ""), caller.get("fileId", ""))
    console.print(Panel(table, title=f"[bold]Impact Analysis for '{symbol_name}'[/bold]"))


@code_graph_app.command("calls")
def code_graph_calls(path: str = typer.Argument(..., help="File or symbol path")) -> None:
    """Find all functions that call a specific function/method."""
    client = _get_client()
    if client:
        result = _call_api(client, "GET", f"{CG_API}/calls/{path}")
        callers = result if isinstance(result, list) else result.get("callers", [])
        if not callers:
            console.print(f"[info]No callers found for '{path}'[/info]")
            return
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Caller", width=30); table.add_column("Type", width=15); table.add_column("File", width=30)
        for caller in callers:
            table.add_row(caller.get("name", ""), caller.get("symbolType", caller.get("symbol_type", "")), caller.get("filePath", caller.get("file_path", "")))
        console.print(Panel(table, title=f"[bold]Callers of '{path}'[/bold]"))
        return

    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    repo = CodeGraphRepository(driver)
    callers = repo.get_callers_by_path(path)
    if not callers:
        console.print(f"[info]No callers found for '{path}'[/info]")
        return
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Caller", width=30); table.add_column("Type", width=15); table.add_column("File", width=30)
    for caller in callers:
        table.add_row(caller.get("name", ""), caller.get("symbolType", ""), caller.get("filePath", ""))
    console.print(Panel(table, title=f"[bold]Callers of '{path}'[/bold]"))


@code_graph_app.command("depends")
def code_graph_depends(path: str = typer.Argument(..., help="File or symbol path")) -> None:
    """Find dependencies (imports) for a file."""
    client = _get_client()
    if client:
        result = _call_api(client, "GET", f"{CG_API}/depends/{path}")
        deps = result if isinstance(result, list) else result.get("dependencies", [])
        if not deps:
            console.print(f"[info]No dependencies found for '{path}'[/info]")
            return
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Module", width=40); table.add_column("Line", width=8); table.add_column("Type", width=10)
        for dep in deps:
            table.add_row(dep.get("module", ""), str(dep.get("line_number", dep.get("line", "-"))), "from" if dep.get("is_from") else "import")
        console.print(Panel(table, title=f"[bold]Dependencies of '{path}'[/bold]"))
        return

    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    repo = CodeGraphRepository(driver)
    deps = repo.get_dependencies_by_path(path)
    if not deps:
        console.print(f"[info]No dependencies found for '{path}'[/info]")
        return
    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Module", width=40); table.add_column("Line", width=8); table.add_column("Type", width=10)
    for dep in deps:
        table.add_row(dep.get("module", ""), str(dep.get("line_number", "-")), "from" if dep.get("is_from") else "import")
    console.print(Panel(table, title=f"[bold]Dependencies of '{path}'[/bold]"))


@code_graph_app.command("tests")
def code_graph_tests(path: str = typer.Argument(..., help="Source file path")) -> None:
    """Find test files related to a source file."""
    client = _get_client()
    if client:
        result = _call_api(client, "GET", f"{CG_API}/tests/{path}")
        tests = result if isinstance(result, list) else result.get("tests", [])
        if not tests:
            console.print(f"[info]No test files found for '{path}'[/info]")
            return
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Test File", width=50); table.add_column("Type", width=15)
        for test in tests:
            table.add_row(test.get("path", ""), test.get("symbolType", test.get("symbol_type", "")))
        console.print(Panel(table, title=f"[bold]Tests for '{path}'[/bold]"))
        return

    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    repo = CodeGraphRepository(driver)
    tests = repo.get_tests_for_file(path)
    if not tests:
        console.print(f"[info]No test files found for '{path}'[/info]")
        return
    table = Table(show_header=True, header_style="bold green")
    table.add_column("Test File", width=50); table.add_column("Type", width=15)
    for test in tests:
        table.add_row(test.get("path", ""), test.get("symbolType", ""))
    console.print(Panel(table, title=f"[bold]Tests for '{path}'[/bold]"))


@code_graph_app.command("file")
def code_graph_file(path: str = typer.Argument(..., help="File path to show details")) -> None:
    """Show detailed information about a file in the graph."""
    client = _get_client()
    if client:
        result = _call_api(client, "GET", f"{CG_API}/files")
        files = result if isinstance(result, list) else result.get("files", [])
        file_data = next((f for f in files if f.get("path") == path or f.get("name") == path), None)
        if not file_data:
            console.print(f"[error]File not found in graph: {path}[/error]")
            raise typer.Exit(code=1)
        console.print(Panel(
            f"[bold]File:[/bold] {file_data.get('name', path)}\n"
            f"[bold]Path:[/bold] {file_data.get('path', 'N/A')}\n"
            f"[bold]Language:[/bold] {file_data.get('language', 'N/A')}\n"
            f"[bold]Lines:[/bold] {file_data.get('lines_of_code', file_data.get('linesOfCode', 0))}\n"
            f"[bold]Hash:[/bold] {str(file_data.get('file_hash', 'N/A'))[:16]}...",
            title="[bold]File Details[/bold]",
        ))
        return

    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository
    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)
    repo = CodeGraphRepository(driver)
    file_data = repo.get_file_by_path(path, "")
    if not file_data:
        console.print(f"[error]File not found in graph: {path}[/error]")
        raise typer.Exit(code=1)
    console.print(Panel(
        f"[bold]File:[/bold] {file_data.get('name', path)}\n"
        f"[bold]Path:[/bold] {file_data.get('path', 'N/A')}\n"
        f"[bold]Language:[/bold] {file_data.get('language', 'N/A')}\n"
        f"[bold]Lines:[/bold] {file_data.get('lines_of_code', 0)}\n"
        f"[bold]Hash:[/bold] {file_data.get('file_hash', 'N/A')[:16]}...",
        title="[bold]File Details[/bold]",
    ))
