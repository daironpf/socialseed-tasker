# Issue #435: Create analysisStore for Impact and RootCause panels

## Description
`ImpactAnalysisPanel.vue` and `RootCausePanel.vue` both use local refs and direct `mockApi` calls. Both independently fetch the full issue/component list, causing redundant network requests. Analysis results are ephemeral and lost on navigation.

## Expected Behavior
- A shared `analysisStore` manages analysis state
- Results are cached and reusable across panels
- Redundant data fetches are eliminated

## Actual Behavior
- `ImpactAnalysisPanel.vue` imports `fetchIssues`, `analyzeImpact` directly
- `RootCausePanel.vue` imports `fetchComponents`, `analyzeRootCause`, `fetchTestFailures` directly
- Both maintain independent local state for results

## Status: TODO

## Priority: LOW

## Component
Frontend / Architecture

## Acceptance Criteria
1. Create `frontend/src/stores/analysisStore.ts` with:
   - `analyzeImpact(issueId)` — calls `mockApi.analyzeImpact()`, caches result
   - `analyzeRootCause(componentId)` — calls `mockApi.analyzeRootCause()`, caches result
   - `fetchTestFailures()` — calls `mockApi.fetchTestFailures()`
   - `clearResults()` — resets cached analysis
2. Refactor `ImpactAnalysisPanel.vue` to use `useAnalysisStore()`
3. Refactor `RootCausePanel.vue` to use `useAnalysisStore()`
4. `npm run build` passes without errors

## Related Issues
- #431: Unify API layer — Pinia stores
