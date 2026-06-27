Neo4j Adapter

Purpose
- Implements GraphPort using the official neo4j Python driver.
- Centralizes Cypher queries and maps driver results to NodeRecord and QueryResult.

Configuration environment variables
- TASKER_NEO4J_URI default bolt://localhost:7687
- TASKER_NEO4J_USER default neo4j
- TASKER_NEO4J_PASSWORD default neoSocial
- TASKER_NEO4J_MAX_RETRIES default 3
- TASKER_NEO4J_RETRY_BACKOFF default 0.5

Examples
- Create node
  adapter.create_node("Issue", {"title": "Fix bug"})
- Run arbitrary query
  adapter.run_cypher("MATCH (n:Issue) RETURN n.title AS title", {})

Operational notes
- Adapter uses exponential backoff for transient errors.
- All Neo4j exceptions are wrapped and rethrown as GraphPortError.
- Close the adapter with adapter.close() to release driver resources.

Docker Compose
- Use docker-compose.neo4j.yml to start a local Neo4j for integration tests:
  docker compose -f docker-compose.neo4j.yml up -d
