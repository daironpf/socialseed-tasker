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

- [ ] Remove `component_id` property from Issue entity
- [ ] Implement `(Issue)-[:BELONGS_TO]->(Component)` relationship
- [ ] Implement `(Issue)-[:BLOCKS]->(Issue)` for dependencies (in addition to existing DEPENDS_ON)
- [ ] Update repository layer to create relationships on issue creation
- [ ] Update CLI: `tasker issue create` accepts `--component` name and creates relationship
- [ ] All existing queries continue to work (maintain backward compatibility via virtual property)

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