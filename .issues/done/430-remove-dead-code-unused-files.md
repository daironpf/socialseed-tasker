# Issue #430: Remove dead code and unused files

## Description
The frontend codebase contained several files that were never imported or used anywhere in the application. These included duplicate API modules, unused UI components, and a dead auth module.

## Expected Behavior
All files in the codebase should be actively used by at least one component or view.

## Actual Behavior
The following files had zero references anywhere in the codebase:
- `src/auth.js` — OAuth-style auth, superseded by `authStore.ts`
- `src/api/dependenciesApi.ts` — Never imported by any view
- `src/api/analysisApi.ts` — Never imported (views use `mockApi.ts`)
- `src/components/ui/Button.vue` — Never used
- `src/components/ui/Input.vue` — Never used
- `src/components/ui/Modal.vue` — Never used
- `src/composables/useToast.ts` — Never used

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Code quality

## Changes Made
Deleted all 7 dead code files:
1. `src/auth.js`
2. `src/api/dependenciesApi.ts`
3. `src/api/analysisApi.ts`
4. `src/components/ui/Button.vue`
5. `src/components/ui/Input.vue`
6. `src/components/ui/Modal.vue`
7. `src/composables/useToast.ts`

## Verification
- `npm run build` passes without errors
- All existing functionality unaffected
- Cleaner codebase with less confusion

## Related Issues
- #431: Unify API layer — views should use Pinia stores consistently
