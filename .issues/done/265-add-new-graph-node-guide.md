# Issue #265: Create "How to Add New Graph Node" Guide

## Description

Create a comprehensive guide that explains how to add new nodes, relationships, and repositories to the Tasker graph model. This guide will enable developers to extend the data model following consistent patterns.

### Current State

The project has examples of various node types (Project, Component, Issue, Agent, etc.) but there's **no documented pattern** for adding new node types. Developers must reverse-engineer existing implementations.

### Requirements

#### Create `docs/IMPLEMENTATION_GUIDE.md`

This document should be the definitive guide for extending the graph model and must include:

```markdown
# Implementation Guide: Adding New Graph Nodes

This guide covers how to add new node types, relationships, and repositories to Tasker.

## Overview

Tasker uses a Property Graph Model with Neo4j. Adding new functionality typically requires:

1. Define the Entity in `core/`
2. Add Cypher queries in `storage/graph_database/queries.py`
3. Implement the Repository in `storage/graph_database/`
4. Add API endpoints in `entrypoints/web_api/routes.py`
5. Add CLI commands in `entrypoints/terminal_cli/`
6. Add Constraints/Indexes in `queries.py`
7. Write tests

## Step-by-Step: Adding a New Node

### Step 1: Define the Entity

Location: `src/socialseed_tasker/core/{module}/entities.py`

Example for adding a "Deployment" node:

```python
class Deployment(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    commit_sha: str
    environment: str
    deployed_at: datetime
    issue_ids: list[UUID] = Field(default_factory=list)
    channel: str | None = None
    deployed_by: str | None = None
```

Follow the pattern:
- Use `frozen=True` for immutability
- Use `Field(default_factory=...)` for dynamic defaults
- Include all properties from the data model
- Add type hints and validation

### Step 2: Add Cypher Queries

Location: `src/socialseed_tasker/storage/graph_database/queries.py`

Add constraint (if not exists):
```python
SCHEMA_CONSTRAINTS = [
    # ... existing
    "CREATE CONSTRAINT deployment_id IF NOT EXISTS FOR (d:Deployment) REQUIRE d.id IS UNIQUE",
]
```

Add index:
```python
SCHEMA_INDEXES = [
    # ... existing
    "CREATE INDEX deployment_commit IF NOT EXISTS FOR (d:Deployment) ON (d.commitSha)",
]
```

Add queries:
```python
CREATE_DEPLOYMENT = """
CREATE (d:Deployment {
    id: $id,
    commitSha: $commit_sha,
    environment: $environment,
    deployedAt: $deployed_at,
    issueIds: $issue_ids,
    channel: $channel,
    deployedBy: $deployed_by
})
RETURN d
"""

GET_DEPLOYMENT = """
MATCH (d:Deployment {id: $id})
RETURN d
"""

# etc.
```

### Step 3: Implement the Repository

Location: `src/socialseed_tasker/storage/graph_database/deployment_repository.py`

```python
class DeploymentRepository:
    def __init__(self, driver: Neo4jDriver) -> None:
        self._driver = driver
    
    def create_deployment(self, deployment: Deployment) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_DEPLOYMENT,
                id=str(deployment.id),
                commit_sha=deployment.commit_sha,
                # ... other params
            )
    
    def get_deployment(self, deployment_id: str) -> Deployment | None:
        # ...
```

### Step 4: Wire into the Container

Location: `src/socialseed_tasker/bootstrap/container.py`

Add the repository to the container:
```python
def create_container() -> Container:
    container = Container()
    container.deployment_repository = DeploymentRepository(container.neo4j_driver)
    return container
```

### Step 5: Add API Endpoints

Location: `src/socialseed_tasker/entrypoints/web_api/routes.py`

```python
@router.post("/deployments", response_model=APIResponse[DeploymentResponse])
def create_deployment(request: DeploymentCreateRequest, repo: TaskRepositoryInterface = Depends(get_repo)):
    # Validate, call action, return response
```

### Step 6: Add CLI Commands (Optional)

Location: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

```python
@cli.command()
def deployment_create(commit_sha: str, environment: str):
    # Call repository, print result
```

### Step 7: Write Tests

Location: `tests/integration/test_deployment.py`

```python
def test_create_deployment():
    # Test the full flow
```

## Common Patterns

### Adding a Relationship

To add a new relationship type (e.g., Deployment -> Issue):

```cypher
# In queries.py
LINK_DEPLOYMENT_TO_ISSUE = """
MATCH (d:Deployment {id: $deployment_id})
MATCH (i:Issue {id: $issue_id})
MERGE (d)-[:DEPLOYED_ISSUES]->(i)
RETURN d, i
"""
```

Then add a repository method:
```python
def link_deployment_to_issue(self, deployment_id: str, issue_id: str) -> None:
    with self._driver.driver.session(database=self._driver.database) as session:
        session.run(queries.LINK_DEPLOYMENT_TO_ISSUE, ...)
```

### Adding Vector Search (RAG)

If the new node needs semantic search:

1. Add vector index in queries.py:
```python
"CREATE VECTOR INDEX deployment_embedding IF NOT EXISTS FOR (d:Deployment) ON (d.embedding)"
```

2. Add embedding property to entity:
```python
embedding: list[float] | None = None
```

3. Use embedding service to generate embeddings on create.

### Adding Policy Enforcement

To enforce policies on the new node:

1. Define rules in `core/project_analysis/policy.py`
2. Add validation in the repository
3. Add endpoint to check violations

## Checklist

- [ ] Entity defined in core/ with all properties
- [ ] Constraints added to SCHEMA_CONSTRAINTS
- [ ] Indexes added to SCHEMA_INDEXES
- [ ] Cypher queries added to queries.py
- [ ] Repository implemented
- [ ] Container updated
- [ ] API endpoints added
- [ ] CLI commands added (if applicable)
- [ ] Tests written
- [ ] Documentation updated (README, API ref)

## Reference Implementation

Study these existing repositories as templates:
- `code_graph_repository.py` - Complex with relationships
- `rag_repository.py` - With vector search
- `reasoning_repository.py` - With feedback pattern

## Common Issues

1. **Case sensitivity**: Neo4j properties are case-sensitive. Use consistent naming (camelCase in DB, snake_case in Python)
2. **UUID vs String**: Store UUIDs as strings in Neo4j, convert in repository
3. **Relationships not creating**: Always use MERGE instead of CREATE for relationships
4. **Missing constraints**: Always add uniqueness constraint for ID fields
```

### Integration Points

Reference existing documentation:
- `Graph Data Model/GraphDataModelDetails.md` - Data model reference
- `.agent/skills/hexagonal-architecture.md` - Architecture rules
- `docs/GRAPH_MODEL.md` - Graph overview

### Business Value

1. **Consistent implementations** - Everyone follows the same pattern
2. **Faster development** - Developers don't need to reverse-engineer
3. **Reduced bugs** - Following proven patterns prevents mistakes
4. **Self-documenting** - The guide explains the "why" behind each step

## Status: PENDING

## Priority: MEDIUM