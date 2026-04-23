# Issue #112: Fix Pre-existing CLI Test Failures

## Description

The CLI tests have 2 pre-existing failures since before v0.8.0. The tests fail with TypeError related to UUID handling in the mock repository patching mechanism.

## Test Failures

| Test | Error | File |
|------|-------|------|
| TestIssueCommands.test_issue_create_success | TypeError: one of the hex, bytes, fields, or int arguments must be given | tests/unit/test_cli_commands.py:159 |
| TestIssueCommands.test_issue_create_missing_component | TypeError: one of the hex, bytes, fields, or int arguments must be given | tests/unit/test_cli_commands.py:175 |

## Requirements

- Fix the UUID handling in test mocks
- Ensure all 232+ unit tests pass
- Add proper mock for the repository

## Status: COMPLETED