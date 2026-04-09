"""Markdown transformer for graph analysis results.

Converts Tasker analysis results into GitHub-flavored Markdown
with tables, Mermaid diagrams, and proper escaping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class MarkdownTable:
    """Represents a Markdown table."""

    headers: list[str]
    rows: list[list[str]]

    def to_markdown(self) -> str:
        """Convert table to Markdown format."""
        if not self.headers:
            return ""

        header_line = "| " + " | ".join(self.headers) + " |"
        separator = "|" + "|".join([" --- " for _ in self.headers]) + "|"

        lines = [header_line, separator]

        for row in self.rows:
            row_line = "| " + " | ".join(row) + " |"
            lines.append(row_line)

        return "\n".join(lines)


class MarkdownTransformer:
    """Transforms graph analysis results to GitHub-flavored Markdown."""

    ESCAPE_CHARS = re.compile(r"([`*_{}\[\]()#+\-.!|>~])")

    @classmethod
    def _escape(cls, text: str) -> str:
        """Escape special Markdown characters."""
        if not isinstance(text, str):
            text = str(text)
        return cls.ESCAPE_CHARS.sub(r"\\\1", text)

    @classmethod
    def transform_root_cause(
        cls,
        causal_links: list[dict[str, Any]],
    ) -> str:
        """Transform root cause analysis to Markdown table.

        Args:
            causal_links: List of causal link dicts with issue, score, reasons

        Returns:
            Markdown table with root cause factors
        """
        if not causal_links:
            return "_No root cause candidates found._"

        headers = ["Issue", "Score", "Reasons"]
        rows: list[list[str]] = []

        for link in causal_links:
            issue = link.get("issue", {})
            issue_title = f"#{issue.get('issue_number', '?')} - {cls._escape(issue.get('title', 'Unknown'))}"
            score = f"{link.get('score', 0):.2f}"
            reasons = cls._escape(", ".join(link.get("reasons", [])))

            rows.append([issue_title, score, reasons])

        table = MarkdownTable(headers=headers, rows=rows)
        return table.to_markdown()

    @classmethod
    def transform_impact(
        cls,
        impact: dict[str, Any],
    ) -> str:
        """Transform impact analysis to Mermaid flowchart.

        Args:
            impact: Impact analysis dict with affected_issues, dependents, risk_level

        Returns:
            Mermaid graph showing impact propagation
        """
        affected = impact.get("affected_issues", [])
        dependents = impact.get("dependents", [])

        if not affected and not dependents:
            return "_No impact analysis data._"

        lines = ["```mermaid", "graph TD"]

        issue_id = impact.get("issue_id", "Issue")

        issue_node = f'    {issue_id}["{cls._escape(issue_id)}"]'
        lines.append(issue_node)

        for i, dep in enumerate(affected[:5]):
            node_id = f"A{i}"
            node_label = f"#{dep.get('issue_number', '?')}"
            lines.append(f'    {node_id}["{cls._escape(node_label)}"]')
            lines.append(f"    {issue_id} --> {node_id}")

        for i, dep in enumerate(dependents[:5]):
            node_id = f"D{i}"
            node_label = f"#{dep.get('issue_number', '?')}"
            lines.append(f'    {node_id}["{cls._escape(node_label)}"]')
            lines.append(f"    {issue_id} --> {node_id}")

        risk = impact.get("risk_level", "unknown")
        lines.append(f"    class {issue_id} risk-{risk}")

        lines.append("```")

        risk_info = f"**Risk Level:** {risk.upper()}"
        if risk == "critical":
            risk_info += " - Immediate action required"
        elif risk == "high":
            risk_info += " - Review within 24h"

        return f"{risk_info}\n\n" + "\n".join(lines)

    @classmethod
    def transform_dependencies(
        cls,
        dependencies: list[dict[str, Any]],
        direction: str = "forward",
    ) -> str:
        """Transform dependency chain to Mermaid graph.

        Args:
            dependencies: List of dependency dicts with source/target issue info
            direction: 'forward' for dependencies, 'backward' for dependents

        Returns:
            Mermaid graph showing dependency chain
        """
        if not dependencies:
            return "_No dependencies._"

        lines = ["```mermaid", "graph LR"]

        for dep in dependencies:
            source = f"#{dep.get('source_number', '?')}"
            target = f"#{dep.get('target_number', '?')}"

            source_safe = cls._escape(source).replace("-", "").replace("#", "")
            target_safe = cls._escape(target).replace("-", "").replace("#", "")

            if direction == "forward":
                lines.append(f'    {source_safe}["{source}"] --> {target_safe}["{target}"]')
            else:
                lines.append(f'    {target_safe}["{target}"] --> {source_safe}["{source}"]')

        lines.append("```")

        return "\n".join(lines)

    @classmethod
    def transform_component_impact(
        cls,
        component_impact: dict[str, Any],
    ) -> str:
        """Transform component impact analysis to Markdown.

        Args:
            component_impact: Component impact dict with component_id, issues, stats

        Returns:
            Markdown with component stats and affected issues table
        """
        component = component_impact.get("component_id", "Unknown")
        stats = component_impact.get("statistics", {})

        lines = [f"## Component: {cls._escape(component)}", ""]

        summary = [
            f"- **Open Issues:** {stats.get('open_issues', 0)}",
            f"- **Total Dependencies:** {stats.get('total_dependencies', 0)}",
            f"- **Avg Priority:** {stats.get('average_priority', 'N/A')}",
        ]
        lines.extend(summary)
        lines.append("")

        issues = component_impact.get("issues", [])
        if issues:
            headers = ["Issue", "Priority", "Status"]
            rows = []

            for issue in issues[:10]:
                number = f"#{issue.get('issue_number', '?')}"
                title = cls._escape(issue.get("title", "")[:40])
                priority = issue.get("priority", "N/A")
                status = issue.get("status", "unknown")

                rows.append([f"{number} {title}", priority, status])

            table = MarkdownTable(headers=headers, rows=rows)
            lines.append(table.to_markdown())

        return "\n".join(lines)

    @classmethod
    def transform_full_analysis(
        cls,
        root_cause: list[dict[str, Any]] | None = None,
        impact: dict[str, Any] | None = None,
        dependencies: list[dict[str, Any]] | None = None,
    ) -> str:
        """Transform complete analysis to comprehensive Markdown report.

        Args:
            root_cause: Root cause analysis results
            impact: Impact analysis results
            dependencies: Dependency chain results

        Returns:
            Complete Markdown report
        """
        sections = []

        if root_cause:
            sections.append("### Root Cause Analysis\n")
            sections.append(cls.transform_root_cause(root_cause))
            sections.append("")

        if impact:
            sections.append("### Impact Analysis\n")
            sections.append(cls.transform_impact(impact))
            sections.append("")

        if dependencies:
            sections.append("### Dependency Chain\n")
            sections.append(cls.transform_dependencies(dependencies))
            sections.append("")

        return "\n".join(sections) if sections else "_No analysis data._"


def transform_root_cause_markdown(causal_links: list[dict[str, Any]]) -> str:
    """Standalone function for root cause transformation."""
    return MarkdownTransformer.transform_root_cause(causal_links)


def transform_impact_markdown(impact: dict[str, Any]) -> str:
    """Standalone function for impact transformation."""
    return MarkdownTransformer.transform_impact(impact)


def transform_dependencies_markdown(
    dependencies: list[dict[str, Any]],
    direction: str = "forward",
) -> str:
    """Standalone function for dependency chain transformation."""
    return MarkdownTransformer.transform_dependencies(dependencies, direction)


_transformer_instance: MarkdownTransformer | None = None


def get_markdown_transformer() -> MarkdownTransformer:
    """Get the global markdown transformer instance."""
    global _transformer_instance
    if _transformer_instance is None:
        _transformer_instance = MarkdownTransformer()
    return _transformer_instance
