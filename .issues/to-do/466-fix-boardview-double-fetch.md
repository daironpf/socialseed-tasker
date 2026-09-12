# Issue #466: BoardView double-fetches issues on mount

## Description
`BoardView.vue` `onMounted` makes two sequential API calls that both fetch issues: first `issuesStore.fetchIssues(1, 500, {})` to load all issues into `allIssues`, then `fetchWithFilters()` which calls `issuesStore.fetchIssues(1, 100, filters)` again, overwriting the store with filtered results. This means two backend calls on every mount, and the second one overwrites the first.

Additionally, `allIssues` is never updated after mount -- if the user creates a new issue while on the Board view, it will not appear in the dashboard charts until they navigate away and back.

## Status: TODO

## Priority: LOW

## Component
Frontend / BoardView

## Acceptance Criteria
1. Remove redundant `issuesStore.fetchIssues(1, 500, {})` call from onMounted
2. Copy `issuesStore.issues` to `allIssues` after `fetchWithFilters()` instead
3. `npm run build` passes

## Related Issues
- None
