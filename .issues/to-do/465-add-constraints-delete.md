# Issue #465: Constraints missing delete capability (incomplete CRUD)

## Description
All other major entities (issues, users, components, policies) have full CRUD operations in the API layer, mock client, and UI. Constraints are the exception: there is no `deleteConstraint` function in `constraintsApi.ts`, no DELETE handler in the mock client, no DELETE endpoint in the mock server, and no delete button in the UI. The ConstraintsView has an edit button per row but no way to remove a constraint.

## Status: TODO

## Priority: MEDIUM

## Component
Backend + Frontend / Constraints

## Acceptance Criteria
1. Add `DELETE /mock/constraints/{id}` endpoint to mock-api server.py
2. Add `deleteConstraint` to mockApi.ts
3. Add `deleteConstraint` to constraintsApi.ts
4. Add DELETE route for constraints in client.ts mock interceptor
5. Add `deleteConstraint` to constraintsStore
6. Add delete button with confirmation to ConstraintsView table rows
7. `npm run build` passes

## Related Issues
- None
