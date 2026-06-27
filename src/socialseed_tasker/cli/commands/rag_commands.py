from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from socialseed_tasker.cli.commands.shared import console, get_repository

rag_app = typer.Typer(help="RAG (Retrieval-Augmented Generation) commands")


@rag_app.command("search")
def rag_search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, "--limit", "-l", help="Maximum results"),
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Minimum similarity score"),
) -> None:
    """Search for similar content using semantic similarity."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)

    repo = RAGRepository(driver)
    results = repo.search(query=query, limit=limit, threshold=threshold)

    if not results:
        console.print("[info]No results found[/info]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Content", width=60)
    table.add_column("Source", width=20)
    table.add_column("Score", width=10)

    for r in results:
        content_preview = r["content"][:57] + "..." if len(r["content"]) > 60 else r["content"]
        table.add_row(content_preview, f"{r['sourceType']}:{r['sourceId'][:8]}", f"{r['score']:.2f}")

    console.print(Panel(table, title=f"[bold]Search Results for '{query}'[/bold]"))


@rag_app.command("index")
def rag_index(
    source_type: str = typer.Option(..., "--type", "-t", help="Source type (issue, adr, code, doc)"),
    source_id: str = typer.Option(..., "--id", "-i", help="Source ID"),
    content: str = typer.Option(..., "--content", "-c", help="Content to index"),
    strategy: str = typer.Option("paragraph", "--strategy", "-s", help="Chunking strategy (paragraph, lines, sentences)"),
) -> None:
    """Index content for RAG semantic search."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)

    repo = RAGRepository(driver)
    repo.create_vector_index()

    chunk_ids = repo.index_text(
        text=content,
        source_type=source_type,
        source_id=source_id,
        chunking_strategy=strategy,
    )

    console.print(f"[success]Indexed {len(chunk_ids)} chunks for {source_type}:{source_id}[/success]")


@rag_app.command("stats")
def rag_stats() -> None:
    """Show RAG index statistics."""
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)

    repo = RAGRepository(driver)
    stats = repo.get_stats()

    console.print(f"[bold]Total embeddings:[/bold] {stats['total']}")
    if stats["by_type"]:
        console.print("[bold]By type:[/bold]")
        for source_type, count in stats["by_type"].items():
            console.print(f"  {source_type}: {count}")


@rag_app.command("clear")
def rag_clear(yes: bool = typer.Option(False, "--yes", "-y", help="Confirm deletion")) -> None:
    """Clear all RAG embeddings."""
    if not yes:
        console.print("[warning]Use --yes to confirm deletion[/warning]")
        return

    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

    driver = get_driver()
    if not driver:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)

    repo = RAGRepository(driver)
    repo.clear()
    console.print("[success]RAG embeddings cleared[/success]")


@rag_app.command("embed-native")
def rag_embed_native(
    source_type: str = typer.Option(..., "--type", "-t", help="Type: issue, symbol, reasoning"),
    source_id: str = typer.Option(..., "--id", "-i", help="Source ID"),
    content: str = typer.Option("", "--content", "-c", help="Content to embed"),
) -> None:
    """Store embedding directly on source node (no separate node).

    This is the optimized approach - stores the embedding
    directly on the Issue/Symbol/ReasoningNode instead of
    creating a separate RAGEmbedding node.
    """
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository
    from socialseed_tasker.infrastructure.neo4j_repository import TaskRepository

    driver = get_driver()
    if driver is None:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)

    if not content:
        repo_task = TaskRepository(driver)
        if source_type == "issue":
            issue = repo_task.get_issue(source_id)
            if issue:
                content = issue.title + " " + issue.description
        if source_type == "reasoning":
            from socialseed_tasker.infrastructure.neo4j_reasoning_repository import ReasoningRepository

            reasoning_repo = ReasoningRepository(driver)
            logs = reasoning_repo.get_reasoning_by_issue(source_id)
            if logs:
                content = " ".join([l.get("thought", "") for l in logs])

    if not content:
        console.print("[error]No content to embed[/error]")
        raise typer.Exit(code=1)

    rag_repo = RAGRepository(driver)
    result = rag_repo.create_native_embedding(source_type, source_id, content)

    if result.get("success"):
        console.print(f"[success]Embedding stored on {source_type}:{source_id}[/success]")
    else:
        console.print(f"[error]{result.get('error')}[/error]")


@rag_app.command("search-native")
def rag_search_native(
    source_type: str = typer.Option("issue", "--type", "-t", help="Type: issue, symbol"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    query: str = typer.Argument(..., help="Search query"),
) -> None:
    """Search using native embeddings (no separate nodes)."""
    from rich.table import Table
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

    driver = get_driver()
    if driver is None:
        console.print("[error]Neo4j not connected[/error]")
        raise typer.Exit(code=1)

    rag_repo = RAGRepository(driver)
    results = rag_repo.search_native(source_type, query, limit)

    if not results:
        console.print("[info]No results found[/info]")
        return

    table = Table(title=f"Native Search Results ({source_type})")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Score", style="green")

    for r in results:
        table.add_row(str(r.get("id", ""))[:8], r.get("title", "")[:30], f"{r.get('score', 0):.3f}")
    console.print(table)
