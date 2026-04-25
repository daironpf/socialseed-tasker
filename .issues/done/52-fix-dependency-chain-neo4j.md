# Issue #52: Fix dependency chain command fails with Neo4j backend

## Description

The `dependency chain` command fails when using the Neo4j backend with error:
```
ValueError: Values of type <class 'uuid.UUID'> are not supported
```

### Command Executed
```bash
tasker --backend neo4j --neo4j-uri "bolt://localhost:17689" --neo4j-password "tasker_password" dependency chain <issue-id>
```

### Expected Behavior
Should display the dependency chain for the issue.

### Actual Behavior
```
ValueError: Values of type <class 'uuid.UUID'> are not supported
```

### Technical Details

The error occurs in `core/task_management/actions.py` in `get_dependency_chain_action`:
```python
dep_issue = repository.get_issue(current_id)
```

The issue is that when the repository returns an Issue with UUID objects, and then passes those UUIDs back to Neo4j queries, the UUID type is not supported by the Neo4j Python driver.

### Solution

Need to convert UUID objects to strings before passing to Neo4j queries. Check the Neo4j repository implementation for places where UUID objects might be passed directly to queries.

**Resolution**: Fixed in `core/task_management/actions.py` by converting UUID objects to strings in the `get_dependency_chain_action` function:
- Changed `queue = deque([issue_id])` to `queue = deque([str(issue_id)])`
- Changed `if current_id != issue_id` to `if current_id != str(issue_id)`
- Added `dep_id_str = str(dep.id)` when adding to queue

## Status: COMPLETED