# Issue #30: Add Dependency Remove CLI Command

## Description

The CLI has `dependency add` but there's no `dependency remove` command to remove a dependency relationship between two issues.

### Requirements

- Add `dependency remove` command
- Usage: `tasker dependency remove <issue_id> <depends_on_id>`
- Handle cases: missing issue, missing dependency, success
- Add tests

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

New command:
```python
@dependency_app.command("remove")
def dependency_remove(
    issue_id: str,
    depends_on_id: str,
) -> None: ...
```

### Business Value

Complete dependency CRUD - users can add AND remove dependencies.

## STATUS: COMPLETED