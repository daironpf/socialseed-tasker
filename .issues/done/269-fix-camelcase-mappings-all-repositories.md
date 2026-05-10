# Issue #269: Fix CamelCase Property Mappings in All Repositories

**Version:** 1.0.1
**Priority:** HIGH
**Status:** COMPLETED
**Assignee:** Agent

## Description
Neo4j stores properties in camelCase (e.g., `componentId`, `createdAt`) but Python models use snake_case (e.g., `component_id`, `created_at`). Multiple repositories were failing with KeyError when reading from Neo4j.

## Tasks
- [x] Fix `_node_to_issue()` in repositories.py - handle componentId/component_id, createdAt/created_at, etc.
- [x] Fix `_node_to_component()` in repositories.py - handle createdAt/created_at, updatedAt/updated_at
- [x] Fix `_node_to_policy()` in policy_repository.py - handle all camelCase properties + add severity field
- [x] Fix `_node_to_commit()` in commit_repository.py - handle authorName/author_name, isAiGenerated/is_ai_generated, filesChanged/files_changed
- [x] Fix `_node_to_user()` in user_repository.py - handle githubHandle/github_handle, createdAt/created_at, lastLogin/last_login
- [x] Fix Cypher query in repositories.py:546 - use `i.componentId` instead of `i.component_id`
- [x] Fix find_issues_by_title NameError - use `component_id` instead of undefined `componentId`

## Success Criteria
- [x] All repository `_node_to_*` functions handle both camelCase (Neo4j) and snake_case (fallback)
- [x] Cypher queries use correct property names (camelCase)
- [x] No more KeyError or NameError when reading from Neo4j

## Solution
Added fallback mappings in all `_node_to_*` functions:
```python
# Example: component_id = data.get("componentId") or data.get("component_id")
```

## Files Modified
- `src/socialseed_tasker/storage/graph_database/repositories.py`
- `src/socialseed_tasker/storage/graph_database/policy_repository.py`
- `src/socialseed_tasker/storage/graph_database/commit_repository.py`
- `src/socialseed_tasker/storage/graph_database/user_repository.py`

## Related
- Issue #268: Fix GET /api/v1/issues list endpoint KeyError
- Finding from real-test evaluation 2026-05-10