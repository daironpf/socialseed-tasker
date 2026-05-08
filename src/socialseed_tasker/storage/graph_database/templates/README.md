# Repository Templates

This directory contains reusable code templates for quickly implementing new repositories in Tasker.

## Templates

| Template | Description | Use Case |
|----------|-------------|----------|
| `simple_crud_repository.py.template` | Basic CRUD operations | Entities with create, read, update, delete |
| `relationship_repository.py.template` | Generic relationship management | Managing links between nodes |
| `queries.py.template` | Cypher query patterns | Ready-to-copy query definitions |

## Quick Start

### 1. Create a Simple Repository

```bash
# Copy the template
cp simple_crud_repository.py.template ../my_entity_repository.py

# Edit and replace placeholders:
# {{ EntityName }} -> YourEntityName
# {{ entity_name }} -> your_entity_name
# {{ entity_description }} -> Description
```

### 2. Create a Relationship Repository

```bash
# Copy the template  
cp relationship_repository.py.template ../my_relationship_repository.py

# Customize for your relationship type:
# - Override methods for specific relationships
# - Add type-safe methods
```

### 3. Copy Queries

```bash
# Copy relevant queries to queries.py
# Replace {{ placeholders }}
```

## Placeholder Reference

| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{{ EntityName }}` | `Deployment` | PascalCase entity name |
| `{{ entity_name }}` | `deployment` | snake_case name |
| `{{ entity_name_upper }}` | `DEPLOYMENT` | Uppercase name |
| `{{ entity_name_snake }}` | `deployment` | Python module name |
| `{{ related_entity }}` | `Issue` | Related node type |
| `{{ relationship_name }}` | `RESOLVED_BY` | Neo4j relationship |
| `{{ module }}` | `deployment_management` | Core module path |
| `{{ properties }}` | `["status", "version"]` | Entity properties |
| `{{ filters }}` | `["status", "project"]` | Filter fields |
| `{{ order_by }}` | `createdAt` | Sort field |

## Example: Creating a Deployment Repository

1. **Copy template:**
   ```bash
   cp templates/simple_crud_repository.py.template ../deployment_repository.py
   ```

2. **Replace placeholders:**
   - `{{ EntityName }}` → `Deployment`
   - `{{ entity_name }}` → `deployment`
   - `{{ entity_description }}` → "Deployment records"

3. **Customize properties:**
   ```python
   class Deployment(BaseModel):
       id: UUID
       commit_sha: str
       environment: str
       deployed_at: datetime
   ```

4. **Add queries to queries.py:**
   ```python
   CREATE_DEPLOYMENT = """..."""
   GET_DEPLOYMENT = """..."""
   ```

5. **Test and use:**
   ```python
   repo = DeploymentRepository(driver)
   repo.create(deployment)
   ```

## See Also

- [Implementation Guide](../../docs/IMPLEMENTATION_GUIDE.md) - Full guide to extending the graph
- [Troubleshooting Guide](../../docs/TROUBLESHOOTING.md) - Common issues and solutions
- [User Repository](../user_repository.py) - Reference implementation
- [Policy Repository](../policy_repository.py) - Reference implementation