from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Any

import typer

from socialseed_tasker.cli.commands.shared import console, get_repository

ISSUE_REF_PATTERN = re.compile(r"#(\d{3,})")

IGNORE_DIRS = {"venv", ".venv", "node_modules", "__pycache__", ".git", ".hg", ".svn", "dist", "build", ".tox", ".eggs", "*.egg-info"}


def doc_sync_command(
    path: str = typer.Argument(".", help="Project root path to scan for documentation"),
) -> None:
    """Scan documentation files and sync their references into the graph.

    Scans .md files in the project, registers them as CodeFile nodes
    in Neo4j, and links any referenced issues.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        console.print(f"[error]Path not found:[/error] {root.as_posix()}")
        raise typer.Exit(code=1)

    md_files = sorted(
        f for f in root.rglob("*.md")
        if not any(part in IGNORE_DIRS for part in f.relative_to(root).parts)
    )

    if not md_files:
        console.print(f"[warning]No .md files found in {root}[/warning]")
        return

    console.print(f"[info]Scanning {len(md_files)} documentation files in {root}...[/info]")

    from socialseed_tasker.infrastructure.neo4j_code_graph_repository import CodeGraphRepository

    try:
        repo = get_repository()
        driver = None
        try:
            from socialseed_tasker.application.wiring import get_driver
            driver = get_driver()
        except Exception:
            pass
    except Exception as exc:
        console.print(f"[warning]Could not connect to graph (reports only): {exc}[/warning]")
        driver = None

    code_repo = CodeGraphRepository(driver) if driver else None
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime())

    total_files = 0
    total_refs = 0
    total_linked = 0
    file_details: list[dict[str, Any]] = []

    for md_file in md_files:
        rel_path = md_file.relative_to(root).as_posix()
        content = md_file.read_text(encoding="utf-8", errors="replace")

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else md_file.stem

        refs = sorted(set(ISSUE_REF_PATTERN.findall(content)))
        refs_str = ", ".join(f"#{r}" for r in refs)

        file_details.append({
            "path": rel_path,
            "title": title,
            "refs": refs,
        })

        if code_repo and rel_path:
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            file_id = hashlib.md5(rel_path.encode()).hexdigest()

            try:
                code_repo._driver.driver.session(
                    database=code_repo._driver.database
                ).run(
                    """MERGE (f:CodeFile {id: $id})
                       SET f.name = $name,
                           f.path = $path,
                           f.language = $language,
                           f.lines_of_code = $lines_of_code,
                           f.file_hash = $file_hash,
                           f.scanned_at = $scanned_at,
                           f.repository_path = $repository_path
                       RETURN f""",
                    {
                        "id": file_id,
                        "name": md_file.name,
                        "path": rel_path,
                        "language": "markdown",
                        "lines_of_code": len(content.splitlines()),
                        "file_hash": file_hash,
                        "scanned_at": now_iso,
                        "repository_path": str(root),
                    },
                )
                total_files += 1
            except Exception as e:
                console.print(f"  [dim]  [!] Could not register {rel_path}: {e}[/dim]")

        total_refs += len(refs)

    # --- Summary ---
    console.print()
    console.print(f"[bold]Documentation Scan Complete[/bold]")
    console.print(f"  [bold]Files found:[/bold] {len(md_files)}")
    console.print(f"  [bold]Files registered:[/bold] {total_files}")
    console.print(f"  [bold]Issue references found:[/bold] {total_refs}")

    if file_details:
        console.print()
        console.print("[bold]Files:[/bold]")
        for fd in file_details:
            refs_str = ", ".join(f"#{r}" for r in fd["refs"])
            icon = "[FILE]" if not fd["refs"] else "[LINK]"
            console.print(f"  {icon} {fd['path']}")
            if refs_str:
                console.print(f"      References: {refs_str}")

    if not driver:
        console.print()
        console.print("[warning]Graph connection not available — files not persisted.[/warning]")
        console.print("[dim]  Run in a project with 'tasker status' showing 'DB: connected'[/dim]")
