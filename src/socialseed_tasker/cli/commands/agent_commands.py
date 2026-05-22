from __future__ import annotations

import os

import typer
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.cli.commands.shared import console, get_repository

agent_app = typer.Typer(help="Agent Integration: context, suggestions, and reasoning")


@agent_app.command("context")
def agent_context(
    issue_id: str = typer.Option(..., "--issue", "-i", help="Issue ID or short ID"),
) -> None:
    """Get code context for an issue from Code-as-Graph."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    driver = get_driver()
    if driver is None:
        console.print("[error]Neo4j not connected. Run 'tasker login' first.[/error]")
        raise typer.Exit(1)

    issue_repo = get_repository()
    issue = issue_repo.get_issue(issue_id)
    if not issue:
        console.print(f"[error]Issue '{issue_id}' not found[/error]")
        raise typer.Exit(1)

    cg_repo = CodeGraphRepository(driver)
    files = cg_repo.get_files(limit=20)

    console.print(Panel("[bold]Code Context[/bold]", border_style="blue"))
    console.print(f"[info]Issue:[/info] {issue.title}")
    console.print(f"[info]Component:[/info] {issue.component_id}")
    console.print(f"\n[bold]Relevant Files ({len(files)}):[/bold]")
    for f in files[:10]:
        console.print(f"  \u2022 {f.get('path', 'unknown')}")


@agent_app.command("suggest")
def agent_suggest(
    issue_id: str = typer.Option(..., "--issue", "-i", help="Issue ID or short ID"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max similar issues to return"),
) -> None:
    """Find similar past issues via RAG."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository
    from socialseed_tasker.domain.entities import ReasoningNode

    driver = get_driver()
    if driver is None:
        console.print("[error]Neo4j not connected. Run 'tasker login' first.[/error]")
        raise typer.Exit(1)

    issue_repo = get_repository()
    issue = issue_repo.get_issue(issue_id)
    if not issue:
        console.print(f"[error]Issue '{issue_id}' not found[/error]")
        raise typer.Exit(1)

    rag_repo = RAGRepository(driver)
    results = rag_repo.search(f"issue {issue.title}", limit=limit)

    console.print(Panel("[bold]Similar Past Issues[/bold]", border_style="blue"))
    console.print(f"[info]Looking for:[/info] {issue.title}")
    if results:
        console.print(f"\n[bold]Found {len(results)} similar issues:[/bold]")
        for r in results:
            console.print(f"  \u2022 {r.get('source_id', 'unknown')}: {str(r.get('content', ''))[:80]}...")
    else:
        console.print("[info]No similar issues found[/info]")


@agent_app.command("reasoning")
def agent_reasoning(
    issue_id: str = typer.Option(..., "--issue", "-i", help="Issue ID"),
    thought: str = typer.Option(..., "--thought", "-t", help="Thought/decision"),
    decision: str = typer.Option("", "--decision", "-d", help="Decision made"),
    decision_type: str = typer.Option("unknown", "--type", "-ty", help="Decision type"),
    alternatives: str = typer.Option(None, "--alternatives", "-alt", help="Comma-separated alternatives considered"),
    rejected: str = typer.Option(None, "--rejected", "-rej", help="Comma-separated reasons for rejecting alternatives"),
) -> None:
    """Log agent reasoning for issue resolution."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.domain.entities import DecisionType, ReasoningNode
    from socialseed_tasker.infrastructure.neo4j_reasoning_repository import ReasoningRepository

    driver = get_driver()
    if driver is None:
        console.print("[error]Neo4j not connected. Run 'tasker login' first.[/error]")
        raise typer.Exit(1)

    issue_repo = get_repository()
    issue = issue_repo.get_issue(issue_id)
    if not issue:
        console.print(f"[error]Issue '{issue_id}' not found[/error]")
        raise typer.Exit(1)

    try:
        decision_type_enum = DecisionType(decision_type)
    except ValueError:
        decision_type_enum = DecisionType.UNKNOWN

    reasoning = ReasoningNode(
        thought=thought,
        confidence=0.8,
        decision=decision,
        decision_type=decision_type_enum,
    )

    repo = ReasoningRepository(driver)
    reasoning_id = repo.log_reasoning(
        issue_id=issue_id,
        agent_id="local-agent",
        agent_name="tasker",
        reasoning=reasoning,
    )

    console.print(f"[success]Logged reasoning for issue {issue_id}[/success]")


@agent_app.command("architect")
def agent_architect(
    issue_id: str = typer.Option(..., "--issue", "-i", help="Issue ID to review"),
    check_only: bool = typer.Option(False, "--check", "-c", help="Only check, don't veto"),
) -> None:
    """ARCHITECT agent: Validate changes against architectural constraints."""
    from rich.panel import Panel

    driver = get_driver()
    if driver is None:
        console.print("[error]Neo4j not connected.[/error]")
        raise typer.Exit(1)

    issue_repo = get_repository()
    issue = issue_repo.get_issue(issue_id)
    if not issue:
        console.print(f"[error]Issue '{issue_id}' not found[/error]")
        raise typer.Exit(1)

    from socialseed_tasker.application.actions import validate_constraints_action
    result = validate_constraints_action(issue_repo)

    if result.violations:
        violations_text = "\n".join([f"- {v.message}" for v in result.violations[:5]])
        console.print(Panel(
            f"[bold red]ARCHITECT VETO: Constraint Violations[/bold red]\n{violations_text}",
            title=f"Architect Review: {issue.title[:30]}",
        ))
        if not check_only:
            console.print("[bold red]Changes blocked pending review.[/bold red]")
        raise typer.Exit(1)
    else:
        console.print(Panel(
            "[bold green]ARCHITECT APPROVED[/bold green]",
            title=f"Architect Review: {issue.title[:30]}",
        ))


@agent_app.command("register")
def agent_register(
    agent_id: str = typer.Option(..., "--id", "-i", help="Unique agent identifier"),
    name: str = typer.Option(..., "--name", "-n", help="Agent name"),
    role: str = typer.Option("developer", "--role", "-r", help="Agent role: developer, reviewer, planner, observer, tester, architect"),
    capabilities: str = typer.Option("", "--capabilities", "-c", help="Comma-separated capabilities"),
    project_id: str | None = typer.Option(None, "--project-id", "-p", help="Optional project ID to assign the agent to"),
) -> None:
    """Register an agent with Tasker to enable tracking and specialization."""
    import httpx

    api_url = os.getenv("TASKER_API_URL", "http://localhost:8000")
    caps = [c.strip() for c in capabilities.split(",") if c.strip()]

    payload = {
        "agent_id": agent_id,
        "name": name,
        "role": role,
        "capabilities": caps,
    }

    if project_id:
        payload["project_id"] = project_id
    else:
        try:
            current_project_resp = httpx.get(f"{api_url}/api/v1/projects/current", timeout=5.0)
            if current_project_resp.status_code == 200:
                project_data = current_project_resp.json()
                if project_data.get("data"):
                    payload["project_id"] = project_data["data"]["id"]
                    console.print(f"[info]Auto-assigning to project:[/info] {project_data['data']['name']} ({project_data['data']['id']})")
        except Exception:
            pass

    try:
        response = httpx.post(
            f"{api_url}/api/v1/agents/register",
            json=payload,
            timeout=10.0,
        )
        if response.status_code == 201:
            data = response.json()
            console.print(f"[success]Agent registered:[/success] {data['data']['agent_id']} ({data['data']['name']})")
            console.print(f"[info]Role:[/info] {data['data']['role']}")
            console.print(f"[info]Capabilities:[/info] {data['data']['capabilities']}")
            if data['data'].get('project_id'):
                console.print(f"[info]Project:[/info] {data['data']['project_id']}")
            else:
                console.print("[warning]No project assigned. Register a project first.[/warning]")
        else:
            console.print(f"[error]Failed to register agent:[/error] {response.text}")
            raise typer.Exit(1)
    except httpx.ConnectError:
        console.print("[error]Cannot connect to API. Is the server running?[/error]")
        raise typer.Exit(1)


@agent_app.command("specialize")
def agent_specialize(
    agent_id: str = typer.Option(..., "--agent", "-a", help="Agent ID"),
    component_id: str = typer.Option(..., "--component", "-c", help="Component ID to specialize in"),
) -> None:
    """Add agent specialization to a component."""
    import httpx

    api_url = os.getenv("TASKER_API_URL", "http://localhost:8000")

    try:
        response = httpx.post(
            f"{api_url}/api/v1/agents/{agent_id}/specialists/{component_id}",
            timeout=10.0,
        )
        if response.status_code in (200, 201):
            console.print(f"[success]Agent {agent_id} specialized in component {component_id}[/success]")
        else:
            console.print(f"[error]Failed:[/error] {response.text}")
            raise typer.Exit(1)
    except httpx.ConnectError:
        console.print("[error]Cannot connect to API.[/error]")
        raise typer.Exit(1)


@agent_app.command("list")
def agent_list() -> None:
    """List all agents registered in Tasker."""
    from rich.table import Table

    api_url = os.getenv("TASKER_API_URL", "http://localhost:8000")
    try:
        response = httpx.get(f"{api_url}/api/v1/agents", timeout=10)
        response.raise_for_status()
        data = response.json()
        agents = data.get("data", [])
    except httpx.ConnectError:
        console.print("[error]Cannot connect to API.[/error]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[error]Failed to list agents: {e}[/error]")
        raise typer.Exit(1)

    if not agents:
        console.print("[info]No agents registered[/info]")
        return

    table = Table(title=f"Agents ({len(agents)})")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Role", style="yellow")
    table.add_column("Status", style="green")

    for agent in agents:
        table.add_row(
            str(agent.get("agent_id", "-"))[:20],
            str(agent.get("name", "-"))[:25],
            str(agent.get("role", "-"))[:15],
            str(agent.get("status", "-"))[:10],
        )
    console.print(table)


@agent_app.command("dispatch")
def agent_dispatch(
    limit: int = typer.Option(5, "--limit", "-l", help="Max issues to dispatch"),
) -> None:
    """Dispatch work: assign OPEN issues to agents."""
    from rich.table import Table

    repo = get_repository()

    open_issues = [i for i in repo.list_issues(statuses=["OPEN"])]
    open_issues.sort(key=lambda x: (
        x.priority.value == "CRITICAL" and 3 or
        x.priority.value == "HIGH" and 2 or
        x.priority.value == "MEDIUM" and 1 or 0
    ), reverse=True)

    if not open_issues:
        console.print("[info]No open issues to dispatch[/info]")
        return

    table = Table(title="Dispatched Issues")
    table.add_column("Issue", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Priority", style="yellow")

    for issue in open_issues[:limit]:
        try:
            repo.update_issue(str(issue.id), {"agent_working": True, "agent_id": "dispatcher"})
            table.add_row(str(issue.id)[:8], issue.title[:30], issue.priority.value)
        except Exception:
            pass

    console.print(table)
