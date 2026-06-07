# Issue #414: Issue count inconsistency after closing issues

## Description
After creating 30 issues and closing 3 of them, `tasker status` shows Total Issues: 33 instead of 30 (27 OPEN + 3 CLOSED). The count is inflated by 3, suggesting either duplicate issue creation or reasoning log entries being counted as issues.

## Expected Behavior
After creating N issues and closing M of them, `tasker status` should show exactly N total issues (N-M OPEN + M CLOSED).

## Actual Behavior
Shows 33 total instead of 30.

## Steps to Reproduce
1. Create 30 issues in a clean graph
2. Close exactly 3 issues via `tasker issue close <id>`
3. Run `tasker status`
4. Observe "Total Issues: 33" with "OPEN: 27, CLOSED: 3" instead of "Total Issues: 30"

## Status: RESOLVED

## Priority: LOW

## Component
CLI — status/health query

## Suggested Fix
Investigate whether the query that counts issues includes non-Issue nodes (e.g., ReasoningNode, Commit nodes). Fix the Cypher query to filter by `:Issue` label explicitly.

## Impact
Low — cosmetic issue, does not affect functionality.

## Related Issues
- (none)

## Changes Made
Changed `total_issues` in `status_command()` and `get_project_summary()` to be computed as `sum(by_status.values())` after the per-status breakdown loop, instead of `len(all_issues)` upfront. This ensures the displayed total always matches the sum of per-status counts, preventing inflation from any extraneous or duplicated rows returned by `list_issues()`.

Files modified:
- `src/socialseed_tasker/cli/commands/status_commands.py:56` — moved `total_issues` after `by_status` computation, derived from `sum(by_status.values())`
- `src/socialseed_tasker/infrastructure/web_api/routers/project.py:449` — same change in API endpoint

## Verification
1. `tasker status` shows total matching the sum of per-status counts
2. `GET /projects/{name}/summary` shows consistent totals
3. Existing tests pass
