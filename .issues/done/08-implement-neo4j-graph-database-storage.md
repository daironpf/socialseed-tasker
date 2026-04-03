# Issue #08: Implement Neo4j Graph Database Storage Layer

## Description

Build the Neo4j storage backend in `src/socialseed_tasker/storage/graph_database/`. This layer implements the `TaskRepositoryInterface` using Neo4j as the persistence engine, leveraging Cypher queries for efficient graph operations.

### Requirements

#### Module Structure

**`driver.py`** - Neo4j connection management
- Async driver initialization and lifecycle management
- Connection pooling configuration
- Health check method
- Graceful shutdown

**`queries.py`** - Cypher query definitions
- All Cypher queries as constants or query builder functions
- Parameterized queries (never string concatenation)
- Organized by entity (issue queries, component queries, relationship queries)

**`repositories.py`** - Repository implementations
- `Neo4jTaskRepository` implementing `TaskRepositoryInterface`
- `Neo4jComponentRepository` implementing component operations

#### Neo4j Graph Schema

**Nodes:**
```cypher
(:Issue {
  id: UUID,
  title: STRING,
  description: STRING,
  status: STRING,
  priority: STRING,
  component_id: UUID,
  labels: LIST<STRING>,
  created_at: DATETIME,
  updated_at: DATETIME,
  closed_at: DATETIME,
  architectural_constraints: LIST<STRING>
})

(:Component {
  id: UUID,
  name: STRING,
  description: STRING,
  project: STRING,
  created_at: DATETIME,
  updated_at: DATETIME
})
```

**Relationships:**
```cypher
(:Issue)-[:DEPENDS_ON]->(:Issue)
(:Issue)-[:BLOCKS]->(:Issue)
(:Issue)-[:AFFECTS]->(:Issue)
(:Issue)-[:BELONGS_TO]->(:Component)
```

#### Repository Implementation Requirements

**Neo4jTaskRepository:**
- `create_issue()` - Create Issue node with all properties
- `get_issue()` - Match Issue by id, return entity
- `update_issue()` - Set properties on existing Issue
- `close_issue()` - Set status=CLOSED, closed_at=now
- `delete_issue()` - Delete Issue node and all its relationships
- `list_issues()` - Match with optional filters, return paginated results
- `add_dependency()` - Create [:DEPENDS_ON] relationship
- `remove_dependency()` - Delete [:DEPENDS_ON] relationship
- `get_dependencies()` - Traverse [:DEPENDS_ON] relationships
- `get_dependents()` - Reverse traverse [:DEPENDS_ON] relationships
- `get_dependency_chain()` - Recursive traversal using APOC `apoc.path.expand` or Cypher variable-length paths
- `detect_circular_dependency()` - Check if adding a dependency would create a cycle

**Neo4jComponentRepository:**
- `create_component()` - Create Component node
- `get_component()` - Match Component by id
- `list_components()` - Match all components with optional project filter

#### APOC Usage
- Use `apoc.date.format()` for datetime formatting where needed
- Use `apoc.path.expand()` or `apoc.path.subgraphAll()` for dependency chain traversal
- Use `apoc.create.setProperty()` for dynamic property updates where needed

#### Error Handling
- Wrap Neo4j-specific exceptions in domain exceptions
- Handle `Neo4jError` for constraint violations, connection issues
- Implement retry logic for transient connection failures
- Log all Cypher queries in debug mode for troubleshooting

### Requirements
- All Neo4j-specific code stays in `storage/graph_database/`
- Must implement the `TaskRepositoryInterface` from core exactly
- No business logic in the storage layer - only data access
- Use parameterized queries exclusively (no Cypher injection)
- Support both sync and async operations where Neo4j driver allows

### Business Value

Neo4j is the primary storage engine that enables the graph-based features of the system: dependency tracking, causal traceability, and architectural integrity checks. The graph structure allows efficient traversal of complex relationships that would be expensive in a relational database. Proper implementation here is critical for performance as the issue graph grows.

## Status: COMPLETED
