# Issue #10: Add CLI Tests for All Commands

## Description

The entire `terminal_cli/commands.py` module has zero test coverage. Every command (issue create/list/show/close/move/delete, dependency add/remove/list/chain/blocked, component create/list/show) is untested.

### Requirements

- Create `tests/unit/test_cli_commands.py`
- Test each CLI command using `typer.testing.CliRunner`
- Test both success and error paths for each command
- Verify Rich output formatting (tables, panels, trees)
- Test the `--json` flag on list commands
- Test the `--force` flag on delete commands
- Test confirmation prompts (with and without `--force`)

### Technical Details

File: `tests/unit/test_cli_commands.py` (new)

Use `CliRunner` from typer:
```python
from typer.testing import CliRunner
from socialseed_tasker.entrypoints.terminal_cli.app import app

runner = CliRunner()

def test_issue_create_success(tmp_path):
    # Setup: create a component first
    result = runner.invoke(app, ["component", "create", "Test", "-p", "proj"])
    assert result.exit_code == 0
    # Extract component ID from output
    # Create issue
    result = runner.invoke(app, ["issue", "create", "Test issue", "-c", component_id])
    assert result.exit_code == 0
    assert "Issue created" in result.stdout

def test_issue_create_missing_component():
    result = runner.invoke(app, ["issue", "create", "Test", "-c", "nonexistent"])
    assert result.exit_code == 2

def test_issue_close_with_open_dependencies():
    # Create two issues, add dependency, try to close
    ...

def test_dependency_add_circular():
    # Create circular dependency, expect error
    ...
```

Commands to test:
- `issue create` (success, missing component, invalid priority)
- `issue list` (with filters, --json, empty)
- `issue show` (existing, missing)
- `issue close` (success, missing, open dependencies, already closed)
- `issue move` (success, missing issue, missing target)
- `issue delete` (with confirmation, --force, missing)
- `dependency add` (success, circular, self-reference, missing)
- `dependency remove` (success, missing)
- `dependency list` (with deps, without)
- `dependency chain` (chain, empty)
- `dependency blocked` (blocked, none)
- `component create` (success, empty name)
- `component list` (with filter, --json)
- `component show` (existing, missing)

Expected file paths:
- `tests/unit/test_cli_commands.py`

### Business Value

The CLI is the primary user interface. Without tests, any refactor to commands.py risks breaking user-facing behavior silently. This is the largest test coverage gap in the project.

## Status: PENDING
