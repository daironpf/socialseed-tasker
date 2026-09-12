# Issue #435: Create analysisStore for Impact and RootCause panels

## Description
`ImpactAnalysisPanel.vue` and `RootCausePanel.vue` both used local refs and direct `mockApi` calls. Both independently fetched the full issue/component list, causing redundant network requests. Analysis results were ephemeral and lost on navigation.

## Expected Behavior
- A shared `analysisStore` manages analysis state
- Results are cached and reusable across panels
- Redundant data fetches are eliminated

## Status: COMPLETED

## Priority: LOW

## Component
Frontend / Architecture

## Changes Made
1. Created `frontend/src/stores/analysisStore.ts` with:
   - `analyzeImpact(issueId)` — calls API, caches result, manages `loadingImpact`
   - `analyzeRootCause(params)` — calls API, caches results, manages `loadingRootCause`
   - `fetchTestFailures()` — calls API, caches failures
   - `clearResults()` — resets cached analysis
2. Refactored `ImpactAnalysisPanel.vue` to use `useAnalysisStore()` and `useIssuesStore()` instead of direct `mockApi` imports
3. Refactored `RootCausePanel.vue` to use `useAnalysisStore()` and `useComponentsStore()` instead of direct `mockApi` imports
4. Removed all direct `mockApi` imports from both components
5. Both components now use existing stores for entity data (issues, components) instead of fetching independently

## Verification
- `npm run build` passes without TypeScript errors
- Analysis results are now managed by the store and persist across component re-renders
- Entity data (issues, components) is fetched through existing stores, eliminating redundant requests

## Related Issues
- #431: Unify API layer — Pinia stores
