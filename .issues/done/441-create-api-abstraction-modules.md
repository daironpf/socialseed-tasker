# Issue #441: Create missing API abstraction modules for stores

## Description
`policiesStore`, `constraintsStore`, `usersStore`, and `analysisStore` imported directly from `mockApi.ts` instead of using proper API abstraction modules. This meant switching `USE_MOCK = false` would break these stores.

## Status: COMPLETED

## Priority: HIGH

## Changes Made
1. Created `frontend/src/api/usersApi.ts` with `fetchUsers()` and `updateUser()`
2. Created `frontend/src/api/constraintsApi.ts` with `fetchConstraints()`, `createConstraint()`, `updateConstraint()`, `validateConstraints()`
3. Created `frontend/src/api/analysisApi.ts` with `analyzeImpact()`, `analyzeRootCause()`, `fetchTestFailures()`
4. Updated `policiesApi.ts` with `deletePolicy()`
5. Updated `policiesStore.ts` to import from `policiesApi.ts`
6. Updated `usersStore.ts` to import from `usersApi.ts`
7. Updated `constraintsStore.ts` to import from `constraintsApi.ts`
8. Updated `analysisStore.ts` to import from `analysisApi.ts`
9. Added all necessary routes to `client.ts` mock interceptor

## Related Issues
- #431: Unify API layer — Pinia stores
