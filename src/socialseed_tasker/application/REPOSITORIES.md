Repository Contracts and Neo4j Implementations

Purpose
- Define IssueRepository and GraphRepository contracts used by application use cases.
- Provide Neo4j-backed implementations that map domain DTOs to graph nodes and relationships.

IssueRepository
- Methods: save(issue), get(issue_id), list(status), delete(issue_id)
- Node label: Issue
- Node property used as primary id: id (string)

GraphRepository
- Methods: add_dependency(edge), get_dependencies(issue_id, depth), find_impact_set(issue_id, max_depth)
- Relationship: DEPENDS_ON
- find_impact_set returns issue ids that transitively depend on the given issue.

Neo4j notes
- All Cypher queries are parameterized.
- Implementations wrap errors as GraphPortError.
- Use docker-compose.neo4j.yml for local integration tests.
