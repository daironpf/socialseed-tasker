# Issue #337: CLI unit tests broken by mandatory authentication check in main.py

## Description

The old argparse-based CLI (`src/socialseed_tasker/cli/main.py`) requires a `--token` argument for every command (lines 296-303). Two unit tests (`test_create_issue_success`, `test_calculate_impact_success`) call `main()` without a token and without expecting `SystemExit`, causing them to crash with `SystemExit(2)`.

Additionally, `test_cli_unauthenticated_returns_error` expects the error to come on stderr as JSON, but the error format may have diverged.

## Expected Behavior

Unit tests that mock the container should be able to test command logic without providing a token, or the auth bypass should be properly mocked.

## Actual Behavior

```
FAILED tests/cli/test_cli_unit.py::test_create_issue_success - SystemExit: 2
FAILED tests/cli/test_cli_unit.py::test_calculate_impact_success - SystemExit: 2
FAILED tests/cli/test_cli_auth.py::test_cli_unauthenticated_returns_error - AssertionError
FAILED tests/cli/test_cli_auth.py::test_cli_forbidden_returns_error - AssertionError
```

## Steps to Reproduce

1. Run `pytest tests/cli/ -q`
2. Observe 4 failures

## Status: PENDING

## Priority: MEDIUM

## Component

CLI — `src/socialseed_tasker/cli/main.py` and `tests/cli/test_cli_unit.py`

## Suggested Fix

Option A: Make token optional in `main()` when running in test mode (e.g. check `PYTEST_CURRENT_TEST` env var).
Option B: Update the success tests to provide a mock token and mock the auth verify method.
Option C: Refactor the auth check to happen inside command functions rather than before dispatch, so mocked commands can bypass it.

## Impact

4 CLI unit tests fail, reducing developer confidence in the CLI layer.
