# Issue #430: Remove dead code and unused files

## Description
The frontend codebase contains several files that are never imported or used anywhere in the application. These include duplicate API modules, unused UI components, and a dead auth module.

## Expected Behavior
All files in the codebase should be actively used by at least one component or view.

## Actual Behavior
The following files are dead code:
- `src/api/auth.js` — OAuth-style auth, superseded by `authStore.ts`
- `src/api/dependenciesApi.ts` — Never imported by any view
- `src/api/analysisApi.ts` — Never imported by any view (views use `mockApi.ts` directly)
- `src/components/ui/Button.vue` — Never used (views implement inline buttons)
- `src/components/ui/Input.vue` — Never used
- `src/components/ui/Modal.vue` — Never used
- `src/composables/useToast.ts` — Never used

## Steps to Reproduce
1. Run `grep -r "auth.js\|dependenciesApi\|analysisApi\|Button.vue\|Input.vue\|Modal.vue\|useToast" src/` — zero results

## Status: OPEN

## Priority: MEDIUM

## Component
Frontend / Code quality

## Suggested Fix
Delete all dead code files listed above. Verify the build still passes after each deletion.

## Impact
Reduced code confusion for new developers; smaller bundle size; cleaner imports.

## Related Issues
- #431: Unify API layer — views should use Pinia stores consistently
