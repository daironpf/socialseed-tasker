"""Integration tests for use cases — exercises real Neo4j repositories and parser adapter.

Requires TASKER_INTEGRATION=1 and Neo4j running via compose/infra/neo4j.yml.
"""

from __future__ import annotations

import os
import textwrap

import pytest

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.application.use_cases import calculate_impact, generate_agent_context
from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from socialseed_tasker.infrastructure.parser_adapter import TreeSitterParser

pytestmark = pytest.mark.integration

NEO4J_URI = os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("TASKER_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("TASKER_NEO4J_PASSWORD", "neoSocial")

PY_SIMPLE = textwrap.dedent("""\
def f():
    return 1
""")


def test_generate_agent_context_end_to_end(tmp_path: pytest.TempPathFactory) -> None:
    graph = Neo4jGraphAdapter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)
    parser = TreeSitterParser()

    fpath = tmp_path / "f.py"
    fpath.write_text(PY_SIMPLE, encoding="utf-8")

    a = IssueDTO(id="issue-a", title="A", description="", status="open", metadata={"files": [str(fpath)]})
    b = IssueDTO(id="issue-b", title="B", description="", status="open", metadata={})
    issue_repo.save(a)
    issue_repo.save(b)
    edge = DependencyEdge(from_issue_id="issue-a", to_issue_id="issue-b", relation="DEPENDS_ON", metadata={})
    graph_repo.add_dependency(edge)

    impact = calculate_impact("issue-b", max_depth=3, graph_repo=graph_repo)
    assert "issue-a" in impact

    ctx = generate_agent_context(
        "issue-b", max_depth=3, graph_repo=graph_repo, issue_repo=issue_repo, parser=parser
    )
    assert ctx["issue"] is not None
    assert "issue-a" in ctx["impact_set"]
    assert "issue-a" in ctx["related_code"]
    assert str(fpath) in ctx["related_code"]["issue-a"]["files"]

    issue_repo.delete("issue-a")
    issue_repo.delete("issue-b")
    graph.close()
