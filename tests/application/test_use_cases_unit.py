"""Unit tests for application use cases — mocks repositories and parser."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from socialseed_tasker.application.dtos import IssueDTO
from socialseed_tasker.application.use_cases import calculate_impact, generate_agent_context


def make_issue(id: str, files: list[str] | None = None) -> IssueDTO:
    return IssueDTO(id=id, title=f"Title {id}", description="", status="open", metadata={"files": files or []})


def test_calculate_impact_calls_graph_repo_and_returns_sorted_unique():
    graph_repo = MagicMock()
    graph_repo.find_impact_set.return_value = ["b", "a", "b"]
    res = calculate_impact("x", max_depth=3, graph_repo=graph_repo)
    assert res == ["a", "b"]


def test_generate_agent_context_includes_issue_and_related_code_and_reasoning():
    graph_repo = MagicMock()
    issue_repo = MagicMock()
    parser = MagicMock()

    graph_repo.find_impact_set.return_value = ["imp-1"]
    issue_repo.get.side_effect = (
        lambda iid: make_issue(iid, files=["/tmp/f1.py"])
        if iid in ("root", "imp-1")
        else None
    )
    parser.parse_file.return_value = {"type": "root", "children": []}
    parser.extract_symbols.return_value = [{"name": "f", "type": "function"}]
    parser.extract_imports.return_value = ["os"]

    ctx = generate_agent_context(
        "root", max_depth=2, graph_repo=graph_repo, issue_repo=issue_repo, parser=parser
    )
    assert "issue" in ctx
    assert "impact_set" in ctx and ctx["impact_set"] == ["imp-1"]
    assert "related_code" in ctx and "imp-1" in ctx["related_code"]
    assert isinstance(ctx["reasoning"], list)
