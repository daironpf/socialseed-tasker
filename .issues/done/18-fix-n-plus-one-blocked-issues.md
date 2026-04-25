# Issue #18: Fix N+1 Query Problem in get_blocked_issues_action

## Description

`get_blocked_issues_action` in `src/socialseed_tasker/core/task_management/actions.py` loads ALL issues from the repository and then calls `repository.get_dependencies()` for each one individually. This creates an N+1 query pattern that scales poorly.

### Requirements

- Refactor `get_blocked_issues_action` to use a single graph traversal query when using Neo4j backend
- For the file backend, optimize by batching dependency lookups
- Add a method to `TaskRepositoryInterface` called `get_blocked_issues() -> list[Issue]` that each backend can implement efficiently
- Write tests verifying the new method returns correct results

### Technical Details

Current implementation in `actions.py:279`:
```python
def get_blocked_issues_action(repo: TaskRepositoryInterface) -> list[Issue]:
    all_issues = repo.list_issues()
    blocked = []
    for issue in all_issues:
        deps = repo.get_dependencies(str(issue.id))  # N queries!
        ...
```

New approach:
```python
# In TaskRepositoryInterface protocol
def get_blocked_issues(self) -> list[Issue]: ...

# In Neo4jTaskRepository - single Cypher query
# MATCH (i:Issue {status: 'OPEN'})-[:DEPENDS_ON]->(d:Issue {status: 'OPEN'})
# RETURN DISTINCT i
```

Expected file paths:
- `src/socialseed_tasker/core/task_management/actions.py`
- `src/socialseed_tasker/storage/graph_database/repositories.py`
- `src/socialseed_tasker/storage/local_files/repositories.py`
- `tests/unit/test_actions.py`

### Business Value

Dramatically improves performance when there are many issues. A project with 500 issues currently triggers 501 queries; this reduces it to 1.

## Status: COMPLETED
