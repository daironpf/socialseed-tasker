# Issue #07: API Schema Synchronization

## Description
The discrepancy between backend pagination and frontend expected types indicates a lack of OpenAPI client generation. Manual TypeScript type maintenance is error-prone.

## Expected Behavior
Implement automated OpenAPI client generation (e.g., using `openapi-typescript` or similar) to ensure frontend and backend type synchronization.

## Actual Behavior
Frontend TypeScript types are manually maintained and can become out of sync with backend API changes, leading to runtime errors like `data.data.forEach is not a function`.

## Steps to Reproduce
1. Change backend API response structure (e.g., pagination format)
2. Run frontend without regenerating types
3. Observe TypeScript compilation errors or runtime errors

## Status: DONE ✓

## Priority: HIGH

## Resolution
- Add `@openapi-ts/openapi-typescript` as dev dependency
- Add `generate-types` script to package.json
- Usage: `npm run generate-types` (requires backend running)
- Generates TypeScript types from OpenAPI spec at /api/v1/openapi.json
- Backend automatically serves OpenAPI spec at /api/v1/openapi.json