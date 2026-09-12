# Issue #436: Add loading and error states to ComponentsView and ConstraintsView

## Description
Both `ComponentsView.vue` and `ConstraintsView.vue` lacked loading spinners during initial data fetch and had no user-facing error messages (only `console.error`). Both stores already exposed `loading` and `error` refs that the templates ignored.

## Expected Behavior
- Loading spinner displayed while data is being fetched
- Error message shown if fetch fails
- Consistent UX with other views

## Status: COMPLETED

## Priority: LOW

## Component
Frontend / UX

## Changes Made
1. `ComponentsView.vue`: Added loading spinner when `compStore.loading` is true
2. `ComponentsView.vue`: Added error banner when `compStore.error` is set
3. `ConstraintsView.vue`: Added loading spinner when `store.loading` is true
4. `ConstraintsView.vue`: Added error banner when `store.error` is set

## Verification
- `npm run build` passes without TypeScript errors
- Both views now show loading spinners during data fetch
- Both views show error messages when fetch fails

## Related Issues
- #433: Refactor ComponentsView to use componentsStore
- #431: Unify API layer — Pinia stores
