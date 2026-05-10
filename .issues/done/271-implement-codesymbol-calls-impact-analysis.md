# Issue #271: Implement CodeSymbol CALLS Impact Analysis

**Version:** 1.0.1
**Priority:** HIGH
**Status:** COMPLETED
**Assignee:** Agent

## Description
The graph model defines the relationship `(CodeSymbol)-[:CALLS]->(CodeSymbol)` which allows the system to identify all methods that depend on a modified method. This is critical for "Impact Analysis" - knowing what else needs testing when code changes. This is now implemented.

## Tasks
- [x] Add endpoint for impact analysis: `POST /api/v1/code/analyze/impact`
- [x] Implement Cypher query for finding callers (direct and transitive)
- [x] Add endpoint to get method callees: `GET /api/v1/code/symbols/{id}/callees`
- [x] Add endpoint to get dependents (who calls this): `GET /api/v1/code/symbols/{id}/callers`
- [x] Add repository methods for impact analysis

## Success Criteria
- [x] Agent can query what methods call a specific method
- [x] Agent can get transitive closure (methods that call indirectly)
- [x] Response includes risk areas that need testing

## Graph Relationship
```
(CodeSymbol)-[:CALLS*1..N]->(CodeSymbol)
```

## API Endpoints
```bash
# Get direct callers (who depends on this)
GET /api/v1/code/symbols/{symbol_id}/callers

# Get transitive callers (full dependency tree)
GET /api/v1/code/symbols/{symbol_id}/callers?transitive=true

# Get callees (what this depends on)
GET /api/v1/code/symbols/{symbol_id}/callees

# Get symbol by ID
GET /api/v1/code/symbols/{symbol_id}

# Full impact analysis
POST /api/v1/code/analyze/impact
Body: {"symbol_id": "uuid", "include_transitive": true}
```

## Risk Levels
- NONE: No callers
- LOW: 1-5 callers
- MEDIUM: 6-20 callers
- HIGH: 20+ callers

## Related
- GraphDataModelDetails.md - Node: CodeSymbol (n7), Relationship: CALLS
- Skill: code-as-graph-analysis.md
- Issue #270: Implement Issue AFFECTS CodeSymbol Link (prerequisite)