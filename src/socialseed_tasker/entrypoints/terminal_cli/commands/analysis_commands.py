"""Analyze commands for root causes and impacts."""

from __future__ import annotations

from typing import Any

import typer
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.entrypoints.terminal_cli.commands.shared import (
    console,
    get_repository,
    resolve_issue_id,
)

# ---------------------------------------------------------------------------
# Analyze commands
# ---------------------------------------------------------------------------

analyze_app = typer.Typer(help="Analyze issues for root causes and impacts")


@analyze_app.command("root-cause")
def analyze_root_cause(
    test_name: str = typer.Option(..., "--test", "-t", help="Test name that failed"),
    error_message: str = typer.Option(..., "--error", "-e", help="Error message from test"),
    component: str = typer.Option("", "--component", "-c", help="Component where test failed"),
    labels: str | None = typer.Option(None, "--labels", "-l", help="Comma-separated test labels"),
) -> None:
    """Analyze test failure to find potential root causes in closed issues."""
    from socialseed_tasker.core.project_analysis.analyzer import RootCauseAnalyzer, TestFailure

    repo = get_repository()
    analyzer = RootCauseAnalyzer(repo)

    all_issues = repo.list_issues()
    closed_issues = [i for i in all_issues if i.status.value == "CLOSED"]

    if not closed_issues:
        console.print("[info]No closed issues found to analyze.[/info]")
        return

    test_failure = TestFailure(
        test_id="cli",
        test_name=test_name,
        error_message=error_message,
        component=component,
        labels=[x.strip() for x in labels.split(",")] if labels else [],
    )

    causal_links = analyzer.find_root_cause(test_failure, closed_issues)

    if not causal_links:
        console.print("[info]No potential root causes found.[/info]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Issue", width=40)
    table.add_column("Confidence", width=12)
    table.add_column("Reasons", width=40)

    for link in causal_links[:10]:
        table.add_row(
            f"{link.issue.title} ({str(link.issue.id)[:8]})",
            f"{link.confidence:.0%}",
            ", ".join(link.reasons[:2]),
        )

    console.print(Panel(table, title=f"[bold]Potential Root Causes ({len(causal_links)} found)[/bold]"))


@analyze_app.command("impact")
def analyze_impact(
    issue_id: str = typer.Argument(..., help="Issue ID (full UUID, 4+ prefix, or exact title)"),
) -> None:
    """Analyze what other issues would be affected by this issue."""
    from socialseed_tasker.core.project_analysis.analyzer import RootCauseAnalyzer

    repo = get_repository()

    try:
        resolved_id = resolve_issue_id(issue_id, repo)
    except ValueError as e:
        console.print(f"[error]{e}[/error]")
        console.print("[info]You can use full UUID, 4+ character prefix, or exact title.[/info]")
        raise typer.Exit(code=2) from e

    analyzer = RootCauseAnalyzer(repo)
    impact = analyzer.analyze_impact(str(resolved_id))

    console.print(
        Panel(
            f"[bold]Directly affected:[/bold] {len(impact.directly_affected)} issues\n"
            f"[bold]Transitively affected:[/bold] {len(impact.transitively_affected)} issues\n"
            f"[bold]Blocked issues:[/bold] {len(impact.blocked_issues)} issues\n"
            f"[bold]Risk level:[/bold] {impact.risk_level.value}",
            title=f"[bold]Impact Analysis for {resolved_id}[/bold]",
            border_style="cyan",
        )
    )

    if impact.directly_affected:
        console.print("\n[bold]Directly affected:[/bold]")
        for issue in impact.directly_affected:
            console.print(f"  - {issue.title} ({issue.status.value})")


@analyze_app.command("code-impact")
def analyze_code_impact(
    path: str = typer.Option(..., "--path", "-p", help="File or directory path"),
) -> None:
    """Analyze code-level impact using Code-as-Graph."""
    from socialseed_tasker.bootstrap.wiring import get_driver
    from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

    driver = get_driver()
    if driver is None:
        console.print("[error]Neo4j not connected. Run 'tasker login' first.[/error]")
        raise typer.Exit(1)

    cg_repo = CodeGraphRepository(driver)

    callers = cg_repo.get_callers_by_path(path)
    dependencies = cg_repo.get_dependencies_by_path(path)
    tests = cg_repo.get_tests_for_file(path)

    risk_level = "CRITICAL" if len(callers) > 5 else "HIGH" if len(callers) > 2 else "MEDIUM" if len(callers) > 0 else "LOW"
    console.print(
        Panel(
            f"[bold]Callers:[/bold] {len(callers)} files\n"
            f"[bold]Dependencies:[/bold] {len(dependencies)} modules\n"
            f"[bold]Test files:[/bold] {len(tests)} files\n"
            f"[bold]Risk level:[/bold] {risk_level}",
            title=f"[bold]Code Impact Analysis for {path}[/bold]",
            border_style="cyan",
        )
    )

    if callers:
        console.print("\n[bold]Files that call this:[/bold]")
        for c in callers[:10]:
            console.print(f"  - {c.get('path', 'unknown')}")

    if dependencies:
        console.print("\n[bold]Dependencies:[/bold]")
        for d in dependencies[:10]:
            console.print(f"  - {d.get('module', 'unknown')}")

    if tests:
        console.print("\n[bold]Test files:[/bold]")
        for t in tests[:10]:
            console.print(f"  - {t.get('path', 'unknown')}")


__all__ = ["analyze_app"]
