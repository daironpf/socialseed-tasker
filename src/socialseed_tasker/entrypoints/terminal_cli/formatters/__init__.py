"""Formatters for CLI output.

Contains table and panel generators for consistent terminal formatting.
"""

from __future__ import annotations

from typing import Any

from rich.box import SIMPLE
from rich.table import Table
from rich.tree import Tree

from socialseed_tasker.core.task_management.entities import Component, Issue


def _issues_table(issues: list[Issue], component_names: dict[str, str] | None = None) -> Table:
    """Generate a formatted table for issues."""
    table = Table(show_header=True, header_style="bold", box=SIMPLE)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Title", width=40)
    table.add_column("Status", width=10)
    table.add_column("Priority", width=8)
    table.add_column("Component", width=20)

    for issue in issues:
        comp_name = ""
        if component_names and str(issue.component_id) in component_names:
            comp_name = component_names[str(issue.component_id)]
        elif component_names is None:
            comp_name = str(issue.component_id)[:8]

        table.add_row(
            str(issue.id)[:8],
            issue.title[:38],
            issue.status.value,
            issue.priority.value,
            comp_name,
        )

    return table


def _components_table(components: list[Component]) -> Table:
    """Generate a formatted table for components."""
    table = Table(show_header=True, header_style="bold", box=SIMPLE)
    table.add_column("Name", width=30)
    table.add_column("Project", width=20)
    table.add_column("Created", width=20)

    for comp in components:
        table.add_row(
            comp.name,
            comp.project,
            comp.created_at.isoformat()[:19],
        )

    return table


def _dependencies_table(
    issue_id: str,
    depends_on: list[dict[str, Any]],
    blocked_by: list[dict[str, Any]],
) -> Table:
    """Generate a formatted table for dependencies."""
    table = Table(show_header=True, header_style="bold", box=SIMPLE)
    table.add_column("Type", width=12)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Title", width=40)
    table.add_column("Status", width=10)

    for dep in depends_on:
        table.add_row(
            "depends on",
            str(dep.get("id", ""))[:8],
            dep.get("title", "")[:38],
            dep.get("status", ""),
        )

    for dep in blocked_by:
        table.add_row(
            "blocked by",
            str(dep.get("id", ""))[:8],
            dep.get("title", "")[:38],
            dep.get("status", ""),
        )

    return table


def _dependency_tree(issue_id: str, deps: list, title: str) -> Tree:
    """Format dependencies as a tree."""
    tree = Tree(f"[bold]{title}[/bold]")
    for dep in deps:
        tree.add(f"{str(dep.get('id', ''))[:8]} - {dep.get('title', '')[:40]}")
    return tree
