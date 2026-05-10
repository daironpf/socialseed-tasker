# Issue #270: Implement Issue AFFECTS CodeSymbol Relationship

**Version:** 1.0.1
**Priority:** HIGH
**Status:** COMPLETED
**Assignee:** Agent

## Description
The graph model in `GraphDataModelDetails.md` defines the relationship `(Issue)-[:AFFECTS]->(CodeSymbol)` which allows agents to know exactly which code symbols are impacted by an issue. This relationship is now implemented.

## Tasks
- [x] Add endpoint to link CodeSymbols to Issues: `POST /api/v1/issues/{id}/affects`
- [x] Add endpoint to get affected symbols: `GET /api/v1/issues/{id}/affects`
- [x] Add query to get issues affecting a CodeSymbol: `GET /api/v1/code/symbols/{id}/issues`
- [x] Update repository with AFFECTS methods
- [x] Add interface methods in TaskRepositoryInterface

## Success Criteria
- [x] Agent can link CodeSymbols to Issue via API
- [x] Agent can query which symbols an issue affects
- [x] Agent can query which issues affect a specific symbol

## Graph Relationship
```
(Issue)-[:AFFECTS]->(CodeSymbol)
```

## API Endpoints
```bash
# Link symbol to issue
POST /api/v1/issues/{issue_id}/affects
Body: {"symbol_id": "uuid"}

# Get affected symbols
GET /api/v1/issues/{issue_id}/affects

# Remove affected symbol
DELETE /api/v1/issues/{issue_id}/affects
Body: {"symbol_id": "uuid"}

# Get issues affecting a symbol
GET /api/v1/code/symbols/{symbol_id}/issues
```

## Related
- GraphDataModelDetails.md - Node: Issue (n5), Relationship: AFFECTS
- Skill: code-as-graph-analysis.md