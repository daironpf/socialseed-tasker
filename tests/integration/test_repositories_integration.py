"""Integration tests for Neo4jIssueRepository and Neo4jGraphRepository.

Requires Neo4j running via compose/infra/neo4j.yml.
"""

import os

import pytest

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository

pytestmark = pytest.mark.integration

NEO4J_URI = os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("TASKER_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("TASKER_NEO4J_PASSWORD", "neoSocial")


def test_issue_and_dependency_flow_integration():
    graph = Neo4jGraphAdapter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)

    a = IssueDTO(id="issue-a", title="A", description="A", status="open", metadata={})
    b = IssueDTO(id="issue-b", title="B", description="B", status="open", metadata={})
    issue_repo.save(a)
    issue_repo.save(b)

    edge = DependencyEdge(from_issue_id="issue-a", to_issue_id="issue-b", relation="DEPENDS_ON", metadata={})
    graph_repo.add_dependency(edge)

    impacted = graph_repo.find_impact_set("issue-b", max_depth=3)
    assert "issue-a" in impacted

    issue_repo.delete("issue-a")
    issue_repo.delete("issue-b")
    graph.close()
