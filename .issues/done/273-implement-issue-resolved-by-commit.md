# Issue #273: Implement Issue RESOLVED_BY Commit Relationship

**Version:** 1.0.1
**Priority:** HIGH
**Status:** COMPLETED
**Assignee:** Agent

## Description
The graph model defines the relationship `(Issue)-[:RESOLVED_BY]->(Commit)` which provides direct linkage between the requirement (issue) and the physical code change (commit) that satisfied it. This is now implemented.

## Tasks
- [x] Update issue close endpoint to accept commit_sha: `POST /api/v1/issues/{id}/close`
- [x] Store commit_sha in Issue entity and Neo4j
- [x] Create the relationship in Neo4j: `(Issue)-[:RESOLVED_BY]->(Commit)`
- [x] Add endpoint to get commit that resolved an issue: `GET /api/v1/issues/{id}/resolution`
- [x] Update issue response to include resolved_by commit info

## Success Criteria
- [x] Closing an issue accepts commit_sha parameter
- [x] Issue displays which commit resolved it
- [x] Full traceability from Issue → Commit

## Graph Relationship
```
(Issue)-[:RESOLVED_BY]->(Commit)
```

## API Endpoints
```bash
# Close issue with commit
curl -X POST "http://localhost:8000/api/v1/issues/{id}/close" \
  -H "Content-Type: application/json" \
  -d '{"commit_sha": "abc123...", "resolution": "implemented"}'

# Get resolution details
curl "http://localhost:8000/api/v1/issues/{id}/resolution"
```

## Implementation Note
This provides the ultimate proof of work. The commit hash links:
- Issue → Commit (what satisfied the requirement)
- Commit → CodeFiles (what was changed)
- Commit → Agent/User (who made the change)
- ReasoningNode → Commit (why the change was made)

This chain enables "Causal Traceability" - knowing exactly why each line of code was changed.

## Related
- GraphDataModelDetails.md - Node: Issue (n5), Relationship: RESOLVED_BY
- Skill: code-as-graph-analysis.md - Causal Traceability section