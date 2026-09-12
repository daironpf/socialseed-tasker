# Issue #432: Create policiesStore and wire PoliciesView

## Description
Policies are the only core entity without a Pinia store. `PoliciesView.vue` manages all state with local `ref<Policy[]>` and calls `policiesApi` directly. Additionally, `mockApi.createPolicy()` never persists to the server — it returns a generated object locally.

## Expected Behavior
- `PoliciesView` uses a `policiesStore` for all data fetching and mutation
- Policy creation persists to the mock API and the JSON file
- Policy state is shared and reusable across views

## Actual Behavior
- `PoliciesView` imports `fetchPolicies` and `createPolicy` from `@/api/policiesApi` directly
- `mockApi.createPolicy()` returns a fake object without server call
- No `policiesStore.ts` exists

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Architecture

## Acceptance Criteria
1. Create `frontend/src/stores/policiesStore.ts` with `fetchPolicies()`, `createPolicy()`, `deletePolicy()`, and computed `activeCount`
2. Add `POST /mock/policies` and `DELETE /mock/policies/{id}` endpoints to `mock-api/server.py` if missing
3. Refactor `PoliciesView.vue` to use `usePoliciesStore()` instead of direct API imports
4. Ensure policy creation persists to `frontend/dataset-de-pruebas/policies.json`
5. `npm run build` passes without errors

## Related Issues
- #431: Unify API layer — Pinia stores
