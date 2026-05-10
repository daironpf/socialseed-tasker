# Issue #268: Fix GET /api/v1/issues list endpoint KeyError

**Version:** 1.0.0
**Priority:** HIGH
**Status:** COMPLETED
**Assignee:** Agent

## Description
The `GET /api/v1/issues` list endpoint throws `KeyError: 'component_id'` when listing issues. This prevents bulk retrieval of issues via the API.

## Tasks
- [x] Fix the mapping in `_node_to_issue()` function in `repositories.py`
- [x] Handle the case difference between `componentId` (Neo4j camelCase) and `component_id` (Python snake_case)
- [x] Add test for list issues endpoint

## Success Criteria
- [x] `GET /api/v1/issues` returns a paginated list of all issues without errors
- [x] All existing tests pass (1 pre-existing failure unrelated to this fix)

## Solution
Updated `_node_to_issue()` in `repositories.py` to handle both camelCase (Neo4j) and snake_case (Python) keys:
- `componentId` / `component_id`
- `createdAt` / `created_at`
- `updatedAt` / `updated_at`
- etc.

## Evidence
```
KeyError: 'component_id'
File "repositories.py", line 64, in _node_to_issue
```

Fixed by using `.get()` with fallback keys.

## Related
- Finding from real-test evaluation 2026-05-10