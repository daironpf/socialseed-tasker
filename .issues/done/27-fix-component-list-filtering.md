# Issue #27: Fix Component List Filtering and Display Issues

## Description

The `component list` command shows all components from all projects, not just the current working set. It should filter by project and show clean output without duplicates. Also the table shows incorrect characters for status (e.g., "CLO" instead of "CLOSED").

### Requirements

- Add project filtering to `component list` by default or add `--all` flag
- Fix the status column display in issue list (characters are being truncated)
- Remove duplicates from component list
- Verify JSON output works correctly

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

Current behavior shows all components globally:
```
$ tasker component list
| Name    | Project      |
|----------+--------------|
| Frontend| project1     |
| Backend | test-project |
...
```

Should filter or show only relevant components.

### Business Value

Users need clean, relevant data. Showing everything confuses users who work on multiple projects.

## STATUS: COMPLETED