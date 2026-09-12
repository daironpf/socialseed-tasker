# Issue #436: Add loading and error states to ComponentsView and ConstraintsView

## Description
Both `ComponentsView.vue` and `ConstraintsView.vue` lack loading spinners during initial data fetch and have no user-facing error messages (only `console.error`). Both stores already expose `loading` and `error` refs that the templates ignore.

## Expected Behavior
- Loading spinner displayed while data is being fetched
- Error message shown if fetch fails
- Consistent UX with other views (e.g., `UsersView` already shows loading spinner)

## Actual Behavior
- `ComponentsView.vue`: No loading spinner during `onMounted` fetch, errors only go to `console.error`
- `ConstraintsView.vue`: No loading spinner during `onMounted` fetch, errors only go to `console.error`
- Both stores expose `loading` and `error` but templates never reference them

## Status: TODO

## Priority: LOW

## Component
Frontend / UX

## Acceptance Criteria
1. `ComponentsView.vue` shows `<LoadingSpinner />` while `componentsStore.loading` is true
2. `ComponentsView.vue` shows error message when `componentsStore.error` is set
3. `ConstraintsView.vue` shows `<LoadingSpinner />` while `constraintsStore.loading` is true
4. `ConstraintsView.vue` shows error message when `constraintsStore.error` is set
5. `npm run build` passes without errors

## Related Issues
- #433: Refactor ComponentsView to use componentsStore
- #431: Unify API layer — Pinia stores
