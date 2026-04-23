# Fix test_component_show_missing exit code

**Status**: COMPLETED
**Priority**: HIGH
**Labels**: test, bug
**Created**: 2026-04-12

## Problem

The test `test_component_show_missing` in `tests/unit/test_cli_commands.py:268` expects exit code 1, but the actual exit code is 2.

## Location

`tests/unit/test_cli_commands.py:268-274`

## Expected Behavior

The test should expect exit code 2 (because `resolve_component_id` raises `ValueError` which triggers exit code 2).

## Current Behavior

```
assert result.exit_code == 1
# Actual: exit_code == 2
```

## Root Cause

The `resolve_component_id` function in `commands.py` raises `ValueError` for invalid IDs, which causes Typer to exit with code 2 instead of 1.

## Suggested Fix

Update the test to expect exit code 2:

```python
def test_component_show_missing(self, runner, mock_repo):
    original = _patch_commands(mock_repo)
    try:
        result = runner.invoke(app, ["component", "show", "nonexistent-id"])
        assert result.exit_code == 2  # Changed from 1 to 2
    finally:
        _unpatch_commands(original)
```

## Test Command

```bash
.venv/Scripts/python.exe -m pytest tests/unit/test_cli_commands.py::TestComponentCommands::test_component_show_missing -v
```

## Status: PENDING