# Issue #06: Add Transaction Boundaries for Issue State Changes

## Description

`close_issue_action` reads dependencies, validates they are all closed, then closes the issue. Between the read and the write, another process could change dependency state. The file backend has no transaction support at all. This creates a race condition where an issue can be closed while still having open dependencies.

### Requirements

- Add a `transaction()` context manager to `TaskRepositoryInterface`
- Implement transaction support in `FileTaskRepository` (file-level lock)
- Implement transaction support in `Neo4jTaskRepository` (native Neo4j transactions)
- Wrap `close_issue_action` in a transaction that re-validates dependencies before committing
- Apply the same pattern to `add_dependency_action` and `move_issue_action`
- Write concurrent tests that attempt to trigger the race condition

### Technical Details

File: `src/socialseed_tasker/core/task_management/actions.py`

New protocol method:
```python
class TaskRepositoryInterface(Protocol):
    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Execute operations atomically."""
        ...
```

Usage in close_issue_action:
```python
def close_issue_action(repo: TaskRepositoryInterface, issue_id: str) -> Issue:
    with repo.transaction():
        issue = repo.get_issue(issue_id)
        if issue is None:
            raise IssueNotFoundError(issue_id)
        if issue.status == IssueStatus.CLOSED:
            raise IssueAlreadyClosedError(issue_id)
        deps = repo.get_dependencies(issue_id)
        open_deps = [d for d in deps if d.status != IssueStatus.CLOSED]
        if open_deps:
            raise OpenDependenciesError(issue_id, [d.id for d in open_deps])
        # Re-validate inside transaction before committing
        return repo.close_issue(issue_id)
```

For file backend: use a file lock (fcntl on Unix, msvcrt on Windows)
For Neo4j: use `session.begin_transaction()`

Expected file paths:
- `src/socialseed_tasker/core/task_management/actions.py`
- `src/socialseed_tasker/storage/graph_database/repositories.py`
- `src/socialseed_tasker/storage/local_files/repositories.py`
- `tests/integration/test_neo4j_repository.py`
- `tests/unit/test_file_repository.py`

### Business Value

Prevents data corruption in concurrent scenarios. Critical for any multi-user or multi-agent environment where multiple processes may modify the same issues simultaneously.

## Status: PENDING
