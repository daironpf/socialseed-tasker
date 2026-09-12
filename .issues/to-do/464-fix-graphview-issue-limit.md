# Issue #464: GraphView fetches only 50 issues (inconsistent limit)

## Description
`GraphView.vue` calls `issuesStore.fetchIssues()` with no arguments, which defaults to `limit = 50` (from `issuesApi.ts` default parameter). Other views use higher limits: KanbanView uses 100, BoardView uses 500. If the project has more than 50 issues, the dependency graph will be incomplete -- missing issues and their edges.

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / GraphView

## Acceptance Criteria
1. Change `issuesStore.fetchIssues()` to `issuesStore.fetchIssues(1, 500)` in GraphView
2. `npm run build` passes

## Related Issues
- None
