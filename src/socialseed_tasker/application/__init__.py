"""Application layer - use cases, services, ports, and orchestration."""

from __future__ import annotations

from socialseed_tasker.application.dtos import DependencyEdge, IssueDTO


def generate_agent_context(issue_id: str, max_depth: int = 3) -> dict:
    """Generate structured context for an agent for a given issue."""
    from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
    from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository

    graph = Neo4jGraphAdapter()
    try:
        issue_repo = Neo4jIssueRepository(graph)
        graph_repo = Neo4jGraphRepository(graph)
        issue = issue_repo.get(issue_id)
        if issue is None:
            return {"error": f"Issue {issue_id} not found"}
        deps = graph_repo.get_dependencies(issue_id, depth=max_depth)
        impacted = graph_repo.find_impact_set(issue_id, max_depth=max_depth)
        return {
            "issue": {"id": issue.id, "title": issue.title, "status": issue.status},
            "dependencies": [
                {"from": d.from_issue_id, "to": d.to_issue_id, "relation": d.relation}
                for d in deps
            ],
            "impact_set": impacted,
        }
    finally:
        graph.close()


def calculate_impact(issue_id: str, max_depth: int = 5) -> list[str]:
    """Calculate impact set for an issue (transitive dependents)."""
    from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository

    graph = Neo4jGraphAdapter()
    try:
        graph_repo = Neo4jGraphRepository(graph)
        return graph_repo.find_impact_set(issue_id, max_depth=max_depth)
    finally:
        graph.close()


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
