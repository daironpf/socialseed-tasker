# Issue #204: Graph Dependencies Query Returns Empty

## Description

The `GET /api/v1/graph/dependencies` endpoint returns an empty result (`{"nodes": [], "edges": []}`) despite having issues and dependencies created in the system. This prevents visualization of the dependency graph.

## Problem

The full dependency graph query returns no data:
- Request: `GET /api/v1/graph/dependencies?project=dental-clinic`
- Expected: Returns nodes and edges representing the dependency graph
- Actual: `{"nodes": [], "edges": []}`

Dependencies are correctly created (verified via `/issues/{id}/dependencies` endpoint), but the graph visualization endpoint returns empty.

## Expected Behavior

The graph endpoint should return all issues and their dependency relationships as nodes and edges for visualization purposes.

## Steps to Reproduce

```bash
# Create issues and dependencies
curl -X POST http://localhost:8000/api/v1/issues ...
curl -X POST http://localhost:8000/api/v1/issues/{id}/dependencies ...

# Verify dependencies exist
curl http://localhost:8000/api/v1/issues/{id}/dependencies
# Returns: {"data": {"items": [...]}} - OK

# Query graph
curl http://localhost:8000/api/v1/graph/dependencies?project=dental-clinic
# Returns: {"nodes": [], "edges": []} - EMPTY
```

## Status

**TODO**

## Priority

**HIGH** - Blocks graph visualization

## Component

GRAPH_ENGINE, API

## Acceptance Criteria

- [ ] Graph endpoint returns nodes for all issues
- [ ] Graph endpoint returns edges for all dependency relationships
- [ ] Project filter works for graph queries
- [ ] Graph structure supports frontend visualization

## Suggested Fix

1. Check `GET_DEPENDENCY_GRAPH` query in queries.py
2. Verify Cypher query syntax and node labels
3. Check if query is matching Issue/BELONGS_TO/Component pattern
4. Add debug logging to identify query execution issues
5. Verify relationship type matches (should be DEPENDS_ON or BLOCKS)

## Impact

- Cannot visualize dependency graph in frontend
- Blocks graph-based analysis features
- Affects DX score for dependency_graph_score (currently 6/10)

## Technical Notes

- Graph response format: `{"nodes": [...], "edges": [...]}`
- Nodes should include: id, title, status, component
- Edges should include: source, target (dependency relationships)
- Query may need to use WITH or RETURN clauses differently

## Related Issues

- Issue #53: Add dependency graph visualization (related)
- Real-Test Evaluation: FIND-003 (Dental Clinic System)