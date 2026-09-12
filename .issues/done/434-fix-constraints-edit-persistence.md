# Issue #434: Fix constraints edit persistence (PATCH endpoint)

## Description
Constraint edits in `ConstraintsView.vue` only modified the local array and were lost on page reload. The mock server had no update endpoint for constraints.

## Expected Behavior
- Editing a constraint persists changes to the server and `constraints.json`
- Navigating away and back preserves edits

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Mock API

## Changes Made
1. Added `PATCH /mock/constraints/{id}` endpoint to `mock-api/server.py` — updates constraint in `constraints.json`
2. Added `updateConstraint(id, body)` function to `frontend/src/api/mockApi.ts`
3. Added PATCH route for constraints to `frontend/src/api/client.ts` mock interceptor
4. Added `updateConstraint(id, body)` action to `frontend/src/stores/constraintsStore.ts`
5. Refactored `ConstraintsView` save function to call `store.updateConstraint()` instead of local array mutation

## Verification
- `npm run build` passes without TypeScript errors
- PATCH /mock/constraints/{id} returns updated constraint with new `updated_at` timestamp
- Constraint edits persist to `constraints.json` and survive page reload

## Related Issues
- #431: Unify API layer — Pinia stores
