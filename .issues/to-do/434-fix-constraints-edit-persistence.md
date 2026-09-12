# Issue #434: Fix constraints edit persistence (PATCH endpoint)

## Description
Constraint edits in `ConstraintsView.vue` only modify the local array and are lost on page reload. The mock server has no update endpoint for constraints.

## Expected Behavior
- Editing a constraint persists changes to the server and `constraints.json`
- Navigating away and back preserves edits

## Actual Behavior
- `ConstraintsView.vue` edit function modifies local array only (line 446-454): `"Edit locally for now (no PATCH endpoint for constraints yet)"`
- `mock-api/server.py` has no `PATCH /constraints/{id}` endpoint

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Mock API

## Acceptance Criteria
1. Add `PATCH /mock/constraints/{id}` endpoint to `mock-api/server.py`
2. The endpoint should update the constraint in `frontend/dataset-de-pruebas/constraints.json`
3. Add `updateConstraint()` function to `frontend/src/api/mockApi.ts`
4. Add `updateConstraint()` action to `constraintsStore.ts`
5. Refactor `ConstraintsView` edit to call store's `updateConstraint()` instead of local array mutation
6. `npm run build` passes without errors

## Related Issues
- #431: Unify API layer — Pinia stores
