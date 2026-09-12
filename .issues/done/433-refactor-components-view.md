# Issue #433: Refactor ComponentsView to use existing componentsStore

## Description
A fully-featured `componentsStore` with CRUD already existed at `frontend/src/stores/componentsStore.ts`, but `ComponentsView.vue` completely ignored it and reimplemented all data management with local refs and direct `mockApi` imports. This caused data duplication and cache invalidation issues.

## Expected Behavior
- `ComponentsView` uses `useComponentsStore()` for all data operations
- Component state is shared and consistent across views

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Architecture

## Changes Made
1. Refactored `ComponentsView.vue` to import `useComponentsStore` and `useIssuesStore` instead of direct `mockApi` imports
2. Removed local `ref<Component[]>` and `ref<Issue[]>` — now uses store state
3. Replaced all local CRUD functions (`saveComponent`, `confirmDelete`) with store method calls
4. Removed unused `Issue` type import
5. `filteredComponents` now filters from `compStore.components` instead of local state

## Verification
- `npm run build` passes without TypeScript errors
- All component CRUD operations route through `componentsStore`
- Data flow is now: ComponentsView → componentsStore → componentsApi → client → mockApi

## Related Issues
- #431: Unify API layer — Pinia stores
- #432: Create policiesStore
