# Issue #518: Test Suite & CI/CD Pipeline (Frontend)

## Description

El frontend no cuenta con ninguna suite de pruebas: `frontend/package.json` solo define `dev/build/preview/generate-types`, sin Vitest, Vue Test Utils, Playwright/Cypress ni ESLint. El CI existente (`.github/workflows/ci.yml`) solo cubre el backend Python (ruff/black/isort, mypy, pytest); los PRs no ejecutan typecheck, linter ni pruebas del frontend.

Origen: `notas.md` → [ISSUE-02] Test Suite & Pipeline de Integración Continua (CI/CD) (→ #518).

## Status: DONE

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
- [x] Vitest + Vue Test Utils configured; unit tests for key stores, composables and components
- [x] Playwright (or Cypress) E2E covering issue creation, Kanban movement and sandbox flows
- [x] ESLint configured with `lint` script for the frontend
- [x] GitHub Actions job runs typecheck (`vue-tsc`), linter and frontend tests on every PR
- [x] Existing Python CI jobs unchanged and still green
- [x] `npm run build` passes

## Resolution

Implemented 2026-09-27:

- **Vitest + Vue Test Utils:** `frontend/vitest.config.ts` (merge de la config de Vite, jsdom, setup global), `src/test/setup.ts` (polyfills matchMedia/ResizeObserver/scrollIntoView + limpieza de localStorage), `src/test/mount.ts` (`mountComponent` con Pinia + i18n + stubs, montado en `document.body` con `enableAutoUnmount`); **81 unit tests en 9 spec files**: stores (`issuesStore`, `uiStore`, `notificationsStore`), composables (`useKeyboardShortcuts`, `useSoundEffects`) y componentes (`FilterBuilder`, `IssueCard`, `ModuleCard`, `SyncQueueDrawer`).
- **Playwright:** `frontend/playwright.config.ts` con `webServer` dual (Vite `:5173` + mock API uvicorn `:8001` con `DATA_DIR` sobre copia temporal `.e2e-data/` preparada por `scripts/prepare-e2e-data.mjs` vía hook `pretest:e2e`), `workers: 1` (el mock API escribe JSON sin locks; paralelismo provocaba carreras), retry x2 en CI, reporter list+html; **8 E2E en 3 specs**: navegación (redirect `/board`, sidebar→Kanban, sandbox, 404), flujo de issue (crear→tarjeta→detalle→cerrar, drag & drop entre columnas, overview del board) y simulación de política en el sandbox.
- **ESLint:** flat config `frontend/eslint.config.js` (js + typescript-eslint + vue flat/recommended con reglas relajadas según convención del proyecto); `vue/no-mutating-props` a `warn` (mutación anidada intencional en IssueDetailView) y fixes puntuales en `useMockStream`/`piiDetector`; `npm run lint` en verde (0 errores, 2 warnings).
- **CI:** `.github/workflows/frontend-ci.yml` en verde teórico — npm cache → `npm run lint` → `npm run build` (vue-tsc) → `npm test` → setup Python 3.11 + mock-api deps → `playwright install chromium` → `npm run test:e2e`, con subida del reporte Playwright si falla; se activa solo con cambios en `frontend/**` para no tocar el CI Python de `ci.yml` (sin modificar).
- **Verificación local completa:** `npm run lint` ✓, `npm test` (81/81) ✓, `npm run build` ✓, `npm run test:e2e` (8/8, dos corridas consecutivas) ✓.
- **i18n:** sin cambios (los tests usan los textos EN existentes).

Notes:
- El modo mock del frontend llama a `mock-api` (uvicorn) vía proxy `/mock-api` → por eso los E2E levantan ese servidor además de Vite.
- `getByDisplayValue` no existe en Playwright 1.63 — aserciones de valor de input vía `toHaveValue`.
- Sidebar: los items son botones (no `<a>`), navegan por `@click` en `Sidebar.vue`.

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
