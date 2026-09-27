# Issue #518: Test Suite & CI/CD Pipeline (Frontend)

## Description

El frontend no cuenta con ninguna suite de pruebas: `frontend/package.json` solo define `dev/build/preview/generate-types`, sin Vitest, Vue Test Utils, Playwright/Cypress ni ESLint. El CI existente (`.github/workflows/ci.yml`) solo cubre el backend Python (ruff/black/isort, mypy, pytest); los PRs no ejecutan typecheck, linter ni pruebas del frontend.

Origen: `notas.md` → [ISSUE-02] Test Suite & Pipeline de Integración Continua (CI/CD) (→ #518).

## Status: TODO

## Priority: HIGH

## Component
Frontend / Quality / Testing / CI

## Type
infra / quality

## Implementation
1. **Vitest + Vue Test Utils:** añadir `vitest`, `@vue/test-utils` y `jsdom`; `frontend/vitest.config.ts` (alias Vite, globals, setup file); scripts `test`, `test:watch`, `test:coverage`. Tests prioritarios: stores (`issuesStore` CRUD+filtros, `uiStore` cola offline de #515, `notificationsStore`), composables (`useKeyboardShortcuts`, `useSoundEffects`) y componentes clave (`FilterBuilder`, `IssueCard`, `ModuleCard`, `SyncQueueDrawer`).
2. **Playwright E2E:** `frontend/playwright.config.ts` con `webServer` (Vite dev + backend Docker opcional); flujos principales: crear issue → mover en Kanban → abrir detalle, simular en Policy Sandbox, login mock. Script `test:e2e`.
3. **Linter JS/TS:** ESLint flat config + typescript-eslint + scripts `lint`/`lint:fix` (hoy no existe ningún linter de frontend).
4. **CI de frontend:** job en `.github/workflows/ci.yml` (o `frontend-ci.yml`): install con cache npm → `npm run lint` → `npm run build` (vue-tsc) → `npm test` → E2E en PR; correr en push/PR igual que los jobs de Python.
5. `npm run build` sigue siendo la verificación mínima local mientras se implementa.

## Acceptance Criteria
- [ ] Vitest + Vue Test Utils configured; unit tests for key stores, composables and components
- [ ] Playwright (or Cypress) E2E covering issue creation, Kanban movement and sandbox flows
- [ ] ESLint configured with `lint` script for the frontend
- [ ] GitHub Actions job runs typecheck (`vue-tsc`), linter and frontend tests on every PR
- [ ] Existing Python CI jobs unchanged and still green
- [ ] `npm run build` passes

## Files to Create
- `frontend/vitest.config.ts` + `frontend/src/test/setup.ts`
- `frontend/src/**/*.spec.ts` (stores, composables, componentes clave)
- `frontend/playwright.config.ts` + `frontend/e2e/` (flujos principales)
- `frontend/eslint.config.js`
- `.github/workflows/frontend-ci.yml` (o job `frontend` en `ci.yml`)

## Files to Modify
- `frontend/package.json` — scripts `test`, `test:e2e`, `lint` + devDependencies
- `.github/workflows/ci.yml` — job de frontend si no se crea workflow aparte
- `features.md` — cuando esté done

## Related Issues
- #111 (Integration Tests), #120 (Docker Integration Tests), #124 (Coverage 70%), #196 (Test Coverage Enhancement), #297 (GitHub Actions CI workflow), #298 (Pre-commit, linters & strict typing)
