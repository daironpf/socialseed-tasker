"""Unit tests for Neo4jIssueRepository."""

from unittest.mock import MagicMock

from socialseed_tasker.application.dtos import IssueDTO, IssueSummary
from socialseed_tasker.application.ports import QueryResult
from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository


def test_save_calls_graph_run_cypher():
    graph = MagicMock()
    repo = Neo4jIssueRepository(graph)
    issue = IssueDTO(id="i1", title="T", description="D", status="open", metadata={})
    repo.save(issue)
    assert graph.run_cypher.called


def test_get_returns_issue_when_found():
    graph = MagicMock()
    repo = Neo4jIssueRepository(graph)
    graph.run_cypher.return_value = QueryResult(
        records=[{"id": "i1", "title": "T", "description": "D", "status": "open", "metadata": {}}]
    )
    got = repo.get("i1")
    assert got is not None
    assert got.id == "i1"
    assert got.title == "T"
    assert got.status == "open"


def test_get_returns_none_when_not_found():
    graph = MagicMock()
    repo = Neo4jIssueRepository(graph)
    graph.run_cypher.return_value = QueryResult(records=[])
    assert repo.get("missing") is None


def test_list_returns_summaries():
    graph = MagicMock()
    repo = Neo4jIssueRepository(graph)
    graph.run_cypher.return_value = QueryResult(
        records=[{"id": "i1", "title": "T", "status": "open"}, {"id": "i2", "title": "U", "status": "closed"}]
    )
    results = repo.list()
    assert len(results) == 2
    assert all(isinstance(r, IssueSummary) for r in results)


def test_list_filters_by_status():
    graph = MagicMock()
    repo = Neo4jIssueRepository(graph)
    graph.run_cypher.return_value = QueryResult(records=[{"id": "i1", "title": "T", "status": "open"}])
    results = repo.list(status="open")
    assert len(results) == 1
    assert results[0].status == "open"
    # Verify Cypher included status filter
    call_kwargs = graph.run_cypher.call_args[0][1]
    assert call_kwargs.get("status") == "open"


def test_delete_calls_run_cypher():
    graph = MagicMock()
    repo = Neo4jIssueRepository(graph)
    repo.delete("i1")
    assert graph.run_cypher.called
