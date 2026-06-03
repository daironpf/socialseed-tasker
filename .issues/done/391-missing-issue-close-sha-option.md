# Issue #391: Missing --sha option in issue close CLI command

## Description
The `tasker issue close` command does not support a `--sha` option to link a commit SHA when closing an issue. Only `--affects` is available for file linking.

## Expected Behavior
`tasker issue close <id> --sha <commit-sha>` should accept a commit SHA and link the resolution to the specific commit, enabling bidirectional traceability between issues and git history.

## Actual Behavior
Only `--affects` is available. Any commit reference must be manually tracked outside the system.

## Steps to Reproduce
1. Run: `tasker issue close <id> --sha <sha>`
2. Observe: `Error: No such option: --sha`

## Status: COMPLETED

## Priority: LOW

## Component
CLI (`issue_commands.py`)

## Suggested Fix
Add a `--sha` optional argument to `issue close` CLI command. Store the SHA in the issue's `resolved_by_commit_sha` field when closing. Update the Neo4j repository's `close_issue` method to accept and persist the commit SHA.

## Impact
Minor. Users who want git-issue traceability must manually link commits. Does not affect core functionality.

## Related Issues
- (none)

## Changes Made
Added `sha: str = typer.Option(None, "--sha", ...)` parameter to `issue_close()` in `issue_commands.py:286`. Passed `commit_sha=sha` to `close_issue_action()` on line 311. Output displays truncated SHA when provided.

All downstream layers (action, repository protocol, Neo4j mixin, Cypher queries, API repository, API router, domain entity) already supported `commit_sha` — only the CLI needed wiring.

## Verification
- `tasker issue close <id> --sha <sha>` no longer errors with "No such option: --sha"
- SHA is persisted to Neo4j `resolvedByCommitSha` on the Issue node
- Backward compatible: `tasker issue close <id>` (without --sha) continues to work
