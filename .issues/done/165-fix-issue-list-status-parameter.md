# Issue #165: Fix Issue List Status Parameter Mismatch

## Description
The `tasker issue list` command fails because the CLI passes `status=` to the repository's `list_issues()` method, but the method expects `statuses=` (plural). This is a parameter name mismatch bug.

## Expected Behavior
The `tasker issue list` command should work correctly and filter issues by status.

## Actual Behavior
Error: `Neo4jTaskRepository.list_issues() got an unexpected keyword argument 'status'. Did you mean 'statuses'?`

## Steps to Reproduce
1. Run `tasker issue list` or `tasker issue list --status OPEN`
2. Observe the error about unexpected keyword argument

## Root Cause
In `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`, line 401:
```python
issues = repo.list_issues(component_id=component, status=status_filter, project=project)
```
But `Neo4jTaskRepository.list_issues()` expects `statuses` (plural):
```python
def list_issues(
    self,
    component_id: str | None = None,
    statuses: list[str] | None = None,  # <-- expects "statuses"
    project: str | None = None,
) -> list[Issue]:
```

## Status: PENDING

## Priority: HIGH

## Recommendations
- Change line 401 in `commands.py` from `status=status_filter` to `statuses=[status_filter] if status_filter else None`
- Or wrap status_filter in a list
- Ensure backward compatibility with existing uses
- Add integration test for the fix

## Related Files
- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py` (line 401)
- `src/socialseed_tasker/storage/graph_database/repositories.py` (lines 248-260)