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
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID, uuid4
from datetime import datetime

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
from neo4j import Neo4jDriver
from socialseed_tasker.core.task_management.entities import Deployment

class DeploymentRepository:
    def __init__(self, driver: Neo4jDriver) -> None:
        self._driver = driver
    
    def _get_session(self):
        if hasattr(self._driver, "driver"):
            return self._driver.driver.session(database=self._driver.database)
        return self._driver.session(database="neo4j")
    
    def create_deployment(self, deployment: Deployment) -> None:
        with self._get_session() as session:
            session.run(
                queries.CREATE_DEPLOYMENT,
                id=str(deployment.id),
                commit_sha=deployment.commit_sha,
                environment=deployment.environment,
                deployed_at=deployment.deployed_at.isoformat(),
                issue_ids=[str(i) for i in deployment.issue_ids],
                channel=deployment.channel,
                deployed_by=deployment.deployed_by,
            )
    
    def get_deployment(self, deployment_id: str) -> Deployment | None:
        with self._get_session() as session:
            result = session.run(queries.GET_DEPLOYMENT, id=deployment_id)
            record = result.single()
            if record:
                return Deployment(**dict(record["d"]))
        return None
```

### Step 4: Wire into the Container

Location: `src/socialseed_tasker/bootstrap/wiring.py` or `bootstrap/container.py`

Add the repository to the wiring module:
```python
# In wiring.py
def get_deployment_repository() -> DeploymentRepository:
    driver = get_driver()
    if driver is None:
        raise RuntimeError("Neo4j driver not available")
    return DeploymentRepository(driver)
```

### Step 5: Add API Endpoints

Location: `src/socialseed_tasker/entrypoints/web_api/routes.py`

```python
from socialseed_tasker.storage.graph_database.deployment_repository import DeploymentRepository

deployment_router = APIRouter()

@deployment_router.post(
    "/deployments",
    response_model=APIResponse[DeploymentResponse],
    summary="Create deployment",
)
def create_deployment(
    request: DeploymentCreateRequest,
) -> APIResponse[DeploymentResponse]:
    from socialseed_tasker.bootstrap.wiring import get_deployment_repository
    
    repo = get_deployment_repository()
    deployment = Deployment(
        commit_sha=request.commit_sha,
        environment=request.environment,
        # ... other fields
    )
    repo.create_deployment(deployment)
    
    return APIResponse(
        data=DeploymentResponse(**deployment.model_dump()),
        meta=Meta(request_id=None),
    )
```

Don't forget to register the router in `app.py`:
```python
app.include_router(deployment_router, prefix="/api/v1", tags=["Deployments"])
```

### Step 6: Add CLI Commands (Optional)

Location: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

```python
deployment_app = typer.Typer(help="Deployment Management")

@deployment_app.command("create")
def deployment_create(
    commit_sha: str = typer.Option(..., "--commit", "-c"),
    environment: str = typer.Option(..., "--env", "-e"),
) -> None:
    """Create a new deployment."""
    # Get repository, call create, print result
    
app.add_typer(deployment_app, name="deployment")
```

### Step 7: Write Tests

Location: `tests/integration/test_deployment.py` or `tests/unit/test_deployment.py`

```python
def test_create_deployment():
    # Test the full flow
    deployment = Deployment(
        commit_sha="abc123",
        environment="production",
        deployed_at=datetime.now(),
    )
    repo = get_deployment_repository()
    repo.create_deployment(deployment)
    
    retrieved = repo.get_deployment(str(deployment.id))
    assert retrieved is not None
    assert retrieved.commit_sha == "abc123"
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
    with self._get_session() as session:
        session.run(
            queries.LINK_DEPLOYMENT_TO_ISSUE,
            deployment_id=deployment_id,
            issue_id=issue_id,
        )
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
- [ ] Wiring/Container updated
- [ ] API endpoints added
- [ ] CLI commands added (if applicable)
- [ ] Tests written
- [ ] Documentation updated (README, API ref)

## Reference Implementation

Study these existing repositories as templates:

| Repository | Pattern |
|------------|---------|
| `code_graph_repository.py` | Complex with multiple relationships |
| `rag_repository.py` | With vector search (embeddings) |
| `reasoning_repository.py` | With feedback pattern |
| `user_repository.py` | Simple entity with multiple relationships |
| `commit_repository.py` | Links to multiple node types |
| `policy_repository.py` | Governance and enforcement |

## Common Issues

### 1. Case Sensitivity
Neo4j properties are case-sensitive. Use consistent naming:
- **Database**: camelCase (`commitSha`, `deployedAt`)
- **Python**: snake_case (`commit_sha`, `deployed_at`)
- **Conversion**: Handle in repository layer

### 2. UUID vs String
Store UUIDs as strings in Neo4j, convert in repository:
```python
# In repository
id=str(deployment.id)  # When saving
deployment = Deployment(id=UUID(record["id"]), ...)  # When reading
```

### 3. Relationships Not Creating
Always use `MERGE` instead of `CREATE` for relationships:
```cypher
# Good - creates or matches
MERGE (d)-[:DEPLOYED_ISSUES]->(i)

# Bad - creates duplicate relationships
CREATE (d)-[:DEPLOYED_ISSUES]->(i)
```

### 4. Missing Constraints
Always add uniqueness constraint for ID fields:
```cypher
CREATE CONSTRAINT deployment_id IF NOT EXISTS FOR (d:Deployment) REQUIRE d.id IS UNIQUE
```

### 5. Driver Access Pattern
Handle both wrapper and direct driver access:
```python
def _get_session(self):
    if hasattr(self._driver, "driver"):
        return self._driver.driver.session(database=self._driver.database)
    return self._driver.session(database="neo4j")
```

---

## Related Documentation

- [Graph Data Model Details](../Graph%20Data%20Model/GraphDataModelDetails.md)
- [Hexagonal Architecture](../.agent/skills/hexagonal-architecture.md)
- [Graph Model Overview](GRAPH_MODEL.md)
- [RAG Guide](RAG_GUIDE.md)
- [Code-as-Graph Guide](CODE_GRAPH_GUIDE.md)