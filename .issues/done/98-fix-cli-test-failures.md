# Issue #98: Fix Pre-existing CLI Test Failures

## Description

Two unit tests in `tests/unit/test_cli_commands.py` are failing due to a UUID handling issue in the mock repository patching mechanism. This is a pre-existing issue that was present before the new features (#95-#97) were added.

## Requirements

- Fix the failing test `TestIssueCommands.test_issue_create_success`
- Fix the failing test `TestIssueCommands.test_issue_create_missing_component`
- Ensure all CLI commands work with the current mock repository implementation
- Maintain backward compatibility with existing CLI tests

## Technical Details

### Error Details
```
tests/unit/test_cli_commands.py:159: in test_issue_create_success
    assert result.exit_code == 0
E   AssertionError: assert 1 == 0
E    +  where 1 = <Result TypeError('one of the hex, bytes, bytes_le, fields, or int arguments must be given')>.exit_code

tests/unit/test_cli_commands.py:175: in test_issue_create_missing_component
    assert result.exit_code == 2
E   AssertionError: assert 1 == 2
E    +  where 1 = <Result TypeError: one of the hex, bytes, fields, or int arguments must be given
```

### Root Cause
The issue is in the `_patch_commands` function in `tests/unit/test_cli_commands.py` at line 134. The function patches `commands.get_repository` to return a mock repository, but there's a TypeError related to UUID handling.

### Affected Code
```python
def _patch_commands(mock_repo: MockRepository):
    """Patch commands.get_repository to return mock_repo."""
    from socialseed_tasker.entrypoints.terminal_cli import commands as cmds
    from socialseed_tasker.entrypoints.terminal_cli import app as cli_app

    original = cmds.get_repository
    cmds.get_repository = lambda: mock_repo
    cli_app._cli_container = None
    return original
```

### Expected Behavior
- Both tests should pass with exit code 0
- The mock repository should properly handle UUID generation for components

## Business Value

Having passing tests ensures code quality and prevents regressions. These failures obscure the actual test results.

## Status: COMPLETED