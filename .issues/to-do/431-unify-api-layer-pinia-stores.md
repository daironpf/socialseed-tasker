# Issue #431: Unify API layer — views should use Pinia stores consistently

## Description
The frontend has two separate API pathways: some views use Pinia stores (e.g., `issuesStore`, `componentsStore`) while others import directly from `mockApi.ts` (e.g., UsersView, ConstraintsView, ComponentsView, AnalysisView, IssueDetailView). This creates inconsistency and makes the data flow harder to trace.

## Expected Behavior
All views should fetch and mutate data through Pinia stores, which in turn call the API layer. This provides:
- Single source of truth
- Reactive state management
- Consistent error handling and loading states

## Actual Behavior
Mixed approach:
- `KanbanView`, `ListView`, `BoardView` → use `issuesStore.fetchIssues()`
- `UsersView` → calls `mockApi.fetchUsers()` directly
- `ConstraintsView` → calls `mockApi.fetchConstraints()` directly
- `ComponentsView` → calls `mockApi.fetchComponents()` directly
- `AnalysisView` → calls `mockApi.analyzeImpact()` directly
- `IssueDetailView` → calls both `issuesStore.fetchIssues()` and `mockApi.fetchAgentLogs()`

## Status: OPEN

## Priority: MEDIUM

## Component
Frontend / Architecture

## Suggested Fix
1. Create missing Pinia stores: `usersStore.ts`, `constraintsStore.ts`, `systemStore.ts`
2. Refactor views to use stores instead of direct `mockApi` imports
3. Keep `mockApi.ts` as the low-level API layer that stores call

## Impact
Better code organization; easier to add real API support later; consistent patterns across the codebase.

## Related Issues
- #430: Remove dead code and unused files
