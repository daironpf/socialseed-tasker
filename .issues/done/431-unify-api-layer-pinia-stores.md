# Issue #431: Unify API layer — views should use Pinia stores consistently

## Description
The frontend had two separate API pathways: some views used Pinia stores while others imported directly from `mockApi.ts`. This created inconsistency and made the data flow harder to trace.

## Expected Behavior
All views should fetch and mutate data through Pinia stores, which in turn call the API layer.

## Actual Behavior
Mixed approach:
- `KanbanView`, `ListView`, `BoardView` → used `issuesStore`
- `UsersView` → called `mockApi.fetchUsers()` directly
- `ConstraintsView` → called `mockApi.fetchConstraints()` directly

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Architecture

## Changes Made
1. Created `src/stores/usersStore.ts` — manages users state with `fetchUsers()`, `updateUser()`, computed `humans`, `agents`, `activeAgents`
2. Created `src/stores/constraintsStore.ts` — manages constraints state with `fetchConstraints()`, `createConstraint()`, `validateConstraints()`, computed `hardCount`, `softCount`, `activeCount`
3. Added `User` interface to `src/types/index.ts`
4. Refactored `UsersView.vue` to use `useUsersStore()` instead of direct `mockApi` imports
5. Refactored `ConstraintsView.vue` to use `useConstraintsStore()` instead of direct `mockApi` imports

## Verification
- `npm run build` passes without TypeScript errors
- All views now use Pinia stores consistently
- Data flow is traceable: View → Store → API → mockApi

## Related Issues
- #430: Remove dead code and unused files
