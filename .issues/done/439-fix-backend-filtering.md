# Issue #439: Fix uiStore.getBackendFilters() broken multi-status filtering

## Description
`uiStore.getBackendFilters()` joined status array with commas, but the mock API expected a single value. Priority filtering was not supported at all.

## Status: COMPLETED

## Priority: HIGH

## Changes Made
1. Mock API `get_issues` now accepts comma-separated statuses and filters each one
2. Mock API `get_issues` now accepts priority parameter with comma-separated values
3. `mockApi.fetchIssues` now passes priority parameter
4. `issuesApi.fetchIssues` now accepts and passes priority parameter
5. `issuesStore.fetchIssues` now accepts priority in filters
6. `uiStore.getBackendFilters` now includes priority filter

## Related Issues
- None
