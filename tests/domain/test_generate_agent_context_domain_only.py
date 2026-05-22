"""Domain-level tests for generate_agent_context — pure in-memory fakes."""

from __future__ import annotations

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.application.use_cases import generate_agent_context
from tests.domain.fake_graph_repo import FakeGraphRepository
from tests.domain.fake_issue_repo import FakeIssueRepository
from tests.domain.fake_parser import FakeParser


def test_generate_agent_context_basic() -> None:
    graph = FakeGraphRepository()
    issues = FakeIssueRepository()
    parser = FakeParser()

    issues.save(
        IssueDTO(id="root", title="R", description="", status="open", metadata={"files": ["f1.py"]})
    )
    issues.save(
        IssueDTO(id="child", title="C", description="", status="open", metadata={"files": ["f2.py"]})
    )

    graph.add_dependency(DependencyEdge(from_issue_id="child", to_issue_id="root", relation="DEPENDS_ON"))

    ctx = generate_agent_context("root", 5, graph, issues, parser)

    assert ctx["issue"]["id"] == "root"
    assert "child" in ctx["impact_set"]
    assert "root" in ctx["related_code"]
    assert "child" in ctx["related_code"]
    assert isinstance(ctx["reasoning"], list)
    assert len(ctx["reasoning"]) > 0
