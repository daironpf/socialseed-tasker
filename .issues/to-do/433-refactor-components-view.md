# Issue #433: Refactor ComponentsView to use existing componentsStore

## Description
A fully-featured `componentsStore` with CRUD already exists at `frontend/src/stores/componentsStore.ts`, but `ComponentsView.vue` completely ignores it and reimplements all data management with local refs and direct `mockApi` imports. This causes data duplication and cache invalidation issues.

## Expected Behavior
- `ComponentsView` uses `useComponentsStore()` for all data operations
- Component state is shared and consistent across views

## Actual Behavior
- `ComponentsView.vue` imports `fetchComponents`, `createComponent`, `updateComponent`, `deleteComponent`, `fetchIssues` directly from `mockApi.ts`
- Local `ref<Component[]>` reimplements state management that `componentsStore` already provides

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Architecture

## Acceptance Criteria
1. Refactor `ComponentsView.vue` to use `useComponentsStore()` instead of direct `mockApi` imports
2. Remove duplicate state management code (local `ref<Component[]>`, manual CRUD functions)
3. Preserve all existing UI functionality (table/grid toggle, search, detail panel, create/edit modal)
4. `npm run build` passes without errors

## Related Issues
- #431: Unify API layer — Pinia stores
