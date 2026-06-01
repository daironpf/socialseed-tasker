# Issue #384: `tasker issue list --json` timeout with moderate issue count

## Description
Running `tasker issue list --json` with 46 issues causes the CLI to hang for >30s or timeout. The API responds in <2s, suggesting the issue is in the CLI HTTP client configuration or output rendering, not the backend.

## Expected Behavior
CLI should list issues in a reasonable time (<5s) for moderate project sizes (50-100 issues).

## Actual Behavior
- API: `GET /api/v1/issues?limit=50` returns in ~2s
- CLI: `tasker issue list --json` hangs for 30-40s then times out

## Steps to Reproduce
1. Create 46+ issues in a project
2. `tasker issue list --json`
3. Observe hang/timeout after 30-40s

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Investigate the `httpx` client timeout configuration in the CLI's issue service. Compare with the API response time. Ensure the client timeout is appropriate for the expected response payload size.

## Impact
Users with moderate project sizes (50+ issues) cannot list issues via CLI in a timely manner. Must use API directly.

## Related Issues
- Issue #159 (Refactor API pagination cypher)
- Issue #165 (Fix issue list status parameter)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
