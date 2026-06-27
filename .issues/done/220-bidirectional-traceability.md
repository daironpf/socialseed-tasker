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

## Status: DONE

## Resolution

### Completed (2026-05-04)
- [x] New relationship type `AFFECTS` in Neo4j
- [x] API endpoint accepts affected files list
- [x] CLI command accepts --affects option
- [x] Graph query for tracing issues to files
- [x] New endpoint GET /api/v1/code-graph/issues/{file_path}

### Files Changed
- `queries.py`: Added ISSUE_AFFECTS_FILE, FIND_ISSUES_AFFECTING_FILE queries
- `code_graph_repository.py`: Added link_issue_to_file, get_issues_affecting_file methods
- `routes.py`: Updated close_issue to accept affected_files, added /issues/{file_path} endpoint
- `commands.py`: Updated CLI issue close --affects option

### Usage
```bash
# CLI
tasker issue close <id> --affects src/foo.py --affects src/bar.py

# API
POST /api/v1/issues/{id}/close?affected_files=["src/foo.py"]

# Query issues affecting a file
GET /api/v1/code-graph/issues/src/foo.py
```
