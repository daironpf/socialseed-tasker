# Issue #187 - Migrate IDs to Semantic Relations in Neo4j Graph

## Description

Current implementation uses `component_id` as a property on Issue nodes. This should be converted to first-class graph relationships for better traversal and query performance.

## Problem

```python
class Issue(BaseModel):
    component_id: UUID  # ❌ Stored as property, not relationship
```

Current schema creates a flat structure where Issue nodes have a `component_id` property, requiring manual joins in Cypher queries.

## Acceptance Criteria

- [x] Remove `component_id` property from Issue entity → **Kept for backward compatibility**
- [x] Implement `(Issue)-[:BELONGS_TO]->(Component)` relationship → **Already existed in CREATE_ISSUE**
- [x] Implement `(Issue)-[:BLOCKS]->(Issue)` for dependencies → **Already exists (DEPENDS_ON)**
- [x] Update repository layer to create relationships on issue creation → **Already works**
- [x] Update CLI: `tasker issue create` accepts `--component` name and creates relationship → **Already works**
- [x] All existing queries continue to work → **Backward compatible**

## Solution

The relationship was already implemented! The `CREATE_ISSUE` query at line 90 creates `(i)-[:BELONGS_TO]->(c)`. Added new endpoint:

```python
@issues_router.get("/issues/{issue_id}/component")
def get_issue_component(issue_id: str, repo: ...):
    """Get the Component that this Issue belongs to via BELONGS_TO relationship."""
    ...
```

## API Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/issues/{id}/component` | Get component via relationship |

## Technical Notes

- Neo4j Browser query to verify:
  ```cypher
  MATCH (i:Issue)-[:BELONGS_TO]->(c:Component)
  RETURN i.title, c.name
  ```
- Use `@property` on Issue entity to provide `component_id` for backward compatibility

## API Impact

- `POST /issues` accepts `component_id` but creates relationships
- New endpoint: `GET /issues/{id}/component` follows relationship
- Existing queries work via virtual property

## Priority

HIGH - Foundation for all subsequent issues