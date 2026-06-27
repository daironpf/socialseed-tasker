"""Unit tests for Neo4jGraphRepository."""

from unittest.mock import MagicMock

from socialseed_tasker.application.dtos import DependencyEdge
from socialseed_tasker.application.ports import QueryResult
from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository


def test_add_dependency_calls_run_cypher():
    graph = MagicMock()
    repo = Neo4jGraphRepository(graph)
    edge = DependencyEdge(from_issue_id="a", to_issue_id="b", relation="DEPENDS_ON", metadata={})
    repo.add_dependency(edge)
    assert graph.run_cypher.called


def test_find_impact_set_returns_ids():
    graph = MagicMock()
    repo = Neo4jGraphRepository(graph)
    graph.run_cypher.return_value = QueryResult(records=[{"id": "a"}])
    impacted = repo.find_impact_set("b")
    assert "a" in impacted


def test_get_dependencies_returns_edges():
    graph = MagicMock()
    repo = Neo4jGraphRepository(graph)
    graph.run_cypher.return_value = QueryResult(
        records=[
            {"from_id": "a", "to_id": "b", "relation": "DEPENDS_ON", "metadata": {}},
        ]
    )
    edges = repo.get_dependencies("a")
    assert len(edges) == 1
    assert edges[0].from_issue_id == "a"
    assert edges[0].to_issue_id == "b"


def test_get_dependencies_empty_when_no_edges():
    graph = MagicMock()
    repo = Neo4jGraphRepository(graph)
    graph.run_cypher.return_value = QueryResult(records=[])
    edges = repo.get_dependencies("nonexistent")
    assert edges == []
