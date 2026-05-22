from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.entrypoints.terminal_cli.commands.shared import console, get_repository

reasoning_app = typer.Typer(help="AI Reasoning Log commands")


@reasoning_app.command("log")
def reasoning_log(
    issue_id: str = typer.Option(..., "--issue", "-i", help="Issue ID"),
    thought: str = typer.Option(..., "--thought", "-t", help="Reasoning thought"),
    agent_id: str = typer.Option("agent-1", "--agent", "-a", help="Agent ID"),
    agent_name: str = typer.Option("DevAgent", "--name", "-n", help="Agent name"),
    confidence: float = typer.Option(0.5, "--confidence", "-c", help="Confidence 0.0-1.0"),
    decision: str = typer.Option(None, "--decision", "-d", help="Decision made"),
    decision_type: str = typer.Option("unknown", "--type", "-ty", help="Decision type"),
    alternatives: str = typer.Option(None, "--alternatives", "-alt", help="Comma-separated alternatives considered"),
    rejected: str = typer.Option(None, "--rejected", "-rej", help="Comma-separated reasons for rejecting alternatives"),
) -> None:
    """Log agent reasoning for an issue."""
    from socialseed_tasker.bootstrap.wiring import get_driver
    from socialseed_tasker.core.task_management.entities import DecisionType, ReasoningNode
    from socialseed_tasker.storage.graph_database.reasoning_repository import ReasoningRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    try:
        decision_type_enum = DecisionType(decision_type)
    except ValueError:
        decision_type_enum = DecisionType.UNKNOWN

    alt_list = [a.strip() for a in alternatives.split(",")] if alternatives else []
    rej_list = [r.strip() for r in rejected.split(",")] if rejected else []

    reasoning = ReasoningNode(
        thought=thought,
        confidence=confidence,
        decision=decision,
        decisionType=decision_type_enum,
        alternativesConsidered=alt_list,
        rejectedReasons=rej_list,
    )

    repo = ReasoningRepository(driver)
    reasoning_id = repo.log_reasoning(issue_id, agent_id, agent_name, reasoning)

    console.print(f"[success]Logged reasoning {reasoning_id} for issue {issue_id}[/success]")


@reasoning_app.command("history")
def reasoning_history(
    issue_id: str = typer.Option(None, "--issue", "-i", help="Filter by issue ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
) -> None:
    """Show reasoning history."""
    from socialseed_tasker.bootstrap.wiring import get_driver
    from socialseed_tasker.storage.graph_database.reasoning_repository import ReasoningRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = ReasoningRepository(driver)

    if issue_id:
        history = repo.get_reasoning_by_issue(issue_id, limit)
    else:
        history = repo.get_reasoning_history(limit)

    if not history:
        console.print("[info]No reasoning found[/info]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Issue", width=20)
    table.add_column("Thought", width=40)
    table.add_column("Decision", width=15)
    table.add_column("Confidence", width=10)

    for h in history:
        thought_preview = h["thought"][:37] + "..." if len(h["thought"]) > 40 else h["thought"]
        issue = h.get("issue_id", h.get("issue_title", "N/A"))[:17]
        table.add_row(
            issue,
            thought_preview,
            h.get("decision", "-") or "-",
            f"{h.get('confidence', 0):.2f}",
        )

    console.print(Panel(table, title=f"[bold]Reasoning History ({len(history)} entries)[/bold]"))


@reasoning_app.command("stats")
def reasoning_stats() -> None:
    """Show reasoning decision statistics."""
    from socialseed_tasker.bootstrap.wiring import get_driver
    from socialseed_tasker.storage.graph_database.reasoning_repository import ReasoningRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = ReasoningRepository(driver)
    stats = repo.get_decision_stats()

    if not stats:
        console.print("[info]No reasoning data[/info]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Decision Type", width=30)
    table.add_column("Count", width=10)
    table.add_column("Avg Confidence", width=15)

    for decision_type, data in stats.items():
        table.add_row(decision_type, str(data["count"]), f"{data['avg_confidence']:.2f}")

    console.print(Panel(table, title="[bold]Decision Statistics[/bold]"))


@reasoning_app.command("clear")
def reasoning_clear(
    issue_id: str = typer.Option(None, "--issue", "-i", help="Clear specific issue"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm"),
) -> None:
    """Clear reasoning data."""
    if not yes:
        console.print("[warning]Use --yes to confirm[/warning]")
        return

    from socialseed_tasker.bootstrap.wiring import get_driver
    from socialseed_tasker.storage.graph_database.reasoning_repository import ReasoningRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        return

    repo = ReasoningRepository(driver)
    if issue_id:
        repo.delete_by_issue(issue_id)
        console.print(f"[success]Cleared reasoning for issue {issue_id}[/success]")
    else:
        repo.clear_all()
        console.print("[success]Cleared all reasoning data[/success]")
