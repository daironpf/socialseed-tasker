"""Application layer - use cases, services, ports, and orchestration."""

from __future__ import annotations

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO
from socialseed_tasker.application.use_cases import calculate_impact, generate_agent_context


def create_issue(issue: IssueDTO) -> None:
    """Create or update an issue."""
    from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository

    graph = Neo4jGraphAdapter()
    try:
        issue_repo = Neo4jIssueRepository(graph)
        issue_repo.save(issue)
    finally:
        graph.close()


def add_dependency(edge: DependencyEdge) -> None:
    """Add a dependency edge between two issues."""
    from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository

    graph = Neo4jGraphAdapter()
    try:
        graph_repo = Neo4jGraphRepository(graph)
        graph_repo.add_dependency(edge)
    finally:
        graph.close()
