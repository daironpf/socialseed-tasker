# Issue #432: Create policiesStore and wire PoliciesView

## Description
Policies were the only core entity without a Pinia store. `PoliciesView.vue` managed all state with local refs and called `policiesApi` directly. Additionally, `mockApi.createPolicy()` returned a fake object without persisting to the server.

## Expected Behavior
- `PoliciesView` uses a `policiesStore` for all data fetching and mutation
- Policy creation persists to the mock API and JSON file
- Policy deletion persists to the mock API and JSON file

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Architecture

## Changes Made
1. Created `frontend/src/stores/policiesStore.ts` — manages policies state with `fetchPolicies()`, `createPolicy()`, `deletePolicy()`, computed `activeCount`, `inactiveCount`
2. Added `POST /mock/policies` and `DELETE /mock/policies/{id}` endpoints to `mock-api/server.py`
3. Fixed `mockApi.createPolicy()` — was returning fake object, now calls `POST /mock/policies`
4. Added `mockApi.deletePolicy()` function
5. Added policies routes to `client.ts` mock interceptor (POST, DELETE)
6. Refactored `PoliciesView.vue` to use `usePoliciesStore()` instead of direct API imports
7. Removed unused `Policy` type import from PoliciesView

## Verification
- `npm run build` passes without TypeScript errors
- POST /mock/policies creates and persists policy to policies.json
- DELETE /mock/policies/{id} removes policy from policies.json
- PoliciesView fetches, displays, and creates policies through the store

## Related Issues
- #431: Unify API layer — Pinia stores
