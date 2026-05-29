# Issue #350: CLI and API Issue Lookup Commands Crash with `Error: 'title'`

## Description
All CLI commands that look up existing issues (`issue list`, `issue show`, `issue close`, `dependency chain`) crash with the cryptic error `Error: 'title'`. The REST API endpoint `GET /api/v1/issues` returns a 500 INTERNAL_ERROR with no detail. Issue creation (`issue create`) and reasoning logging (`reasoning log`) work correctly, confirming the bug is in the issue lookup/resolution path.

This finding was discovered during a black-box evaluation (see `real-test/report.md`).

## Expected Behavior
- `tasker issue list` should display all issues
- `tasker issue show <id>` should show issue details
- `tasker issue close <id>` should close the issue
- `tasker dependency chain <id>` should show the dependency chain
- `GET /api/v1/issues` should return the list of issues
- Non-existent IDs should show "Issue not found" messages

## Actual Behavior
```
$ tasker issue list
Error: 'title'

$ tasker issue show a4e836d3
Error: 'title'

$ tasker issue close 8961adba
Error: 'title'

$ tasker dependency chain a4e836d3
Error: 'title'

$ GET /api/v1/issues
{ "data": null, "error": { "code": "INTERNAL_ERROR", "message": "An unexpected error occurred" } }
```

## Steps to Reproduce
1. Install tasker with `pip install -e .` and configure with `tasker init`
2. Create some issues via `tasker issue create`
3. Run `tasker issue list`
4. Observe `Error: 'title'`
5. Try `tasker issue show <any-id>` — same error
6. Try `curl.exe http://localhost:8888/api/v1/issues` — 500 error

## Status: PENDING

## Priority: CRITICAL

## Component
CLI / API (CORE)

## Suggested Fix
1. Check the `find_issue` function in the CLI command layer — the error `'title'` suggests a Click/Typer parameter name mismatch where the Python function parameter is named `title` but the CLI argument is named `issue_id`.
2. Add error handling so that missing or invalid issue IDs produce user-friendly "Issue not found" messages.
3. Fix the `GET /api/v1/issues` endpoint to return proper error details instead of a generic 500.
4. Verify the Cypher queries used for issue lookup handle edge cases (e.g., after a code-graph scan).

## Impact
Issue management is completely blocked. Users cannot list, view, close, or track dependencies on existing issues. The tool is effectively unusable for project management workflows.

## Related Issues
- FIND-002 (report.md): CLI regression
- FIND-003 (report.md): API regression
- FIND-005 (report.md): Non-friendly error messages
