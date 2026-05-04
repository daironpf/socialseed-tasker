# Issue #220: Bidirectional Traceability: Link Issues to Code Graph

## Description
Establish a formal link between `Issue` nodes and `CodeFile`/`CodeSymbol` nodes in the Neo4j graph. When an issue is closed, the system should record which code elements were modified.

## Acceptance Criteria
- [ ] New relationship type `AFFECTS` or `RESOLVED_BY` in Neo4j.
- [ ] API updated to accept list of affected files when closing an issue.
- [ ] CLI `issue close` command updated to optionally take file paths.
- [ ] Graph query to find all issues that touched a specific file.

## Technical Notes
- Leverage the existing `Code-as-Graph` nodes.
- Ensure the relationship is stored in the `TaskRepository`.
