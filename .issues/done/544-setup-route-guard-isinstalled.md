# Issue #544: Navigation guard de instalación y estado `isInstalled` en el frontend

## Description

El frontend en Vue 3 debe interceptar la navegación de las rutas principales (`/`, `/kanban`, `/graph`, …) para redirigir forzosamente a la vista `/setup` si el sistema no ha completado la instalación inicial (servidor `GET /api/v1/setup/status` de #543), y evitar entrar al wizard cuando el sistema ya está instalado.

Contexto real del repo: `router.beforeEach` ya existe y encadena `authStore.initSession()` + control `meta.roles` (#519); el overlay `LoginScreen` cubre la app cuando no hay sesión (`App.vue`), por lo que `/setup` debe quedar exento de login; y en **modo mock** (`isMockMode()`, #517) la demo autoautenticada no debe quedar bloqueada por un guard de primera instalación.

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #3 (→ #544).

## Status: DONE (2026-10-03)

## Priority: HIGH

## Component
Frontend / Router / State

## Type
feat / integration

## Implementation
1. **Módulo API:** `frontend/src/api/setupApi.ts` con `getSetupStatus()` → `GET /setup/status` a través del `client` dual (en mock no llama a la API real).
2. **Persistencia en Pinia (`uiStore.ts`):** propiedades `isInstalled: boolean | null` y `setupChecked: boolean` + acción `checkSetupStatus()` cacheada (una sola llamada HTTP, sin llamadas redundantes en cada cambio de vista).
3. **`router.beforeEach` (`router/index.ts`):** encadenar tras `initSession()`:
   * Si `!isMockMode()` e `isInstalled === false` y la ruta destino **no** es `/setup` → redirigir a `/setup`.
   * Si `installed === true` y la ruta destino **es** `/setup` → redirigir a `/board` (la raíz `/` ya redirige a `/board` en este repo).
4. **Accesibilidad sin sesión:** `App.vue` no debe mostrar `LoginScreen` para `/setup` (el wizard corre antes de tener administrador).
5. **Modo mock:** sin guard (o status tratado como instalado) para preservar la demo intacta.
6. **i18n:** claves de error/loading del guard en EN + ES (ASCII en ES).
7. **Tests:** spec del guard/`uiStore` (vitest): redirección con sistema nuevo, acceso directo a `/setup` instalado, caché de la llamada, mock sin guard.

## Acceptance Criteria
- [x] Abrir la raíz de la aplicación en un navegador con el sistema nuevo redirige inmediatamente a `http://localhost:<FRONTEND_PORT>/setup`
- [x] Con `installed === true`, navegar a `/setup` redirige a `/board`
- [x] `isInstalled` vive en `uiStore` y la consulta se cachea (sin llamadas redundantes por navegación)
- [x] `/setup` es accesible sin iniciar sesión (no bloqueado por `LoginScreen` ni `meta.roles`)
- [x] El modo mock conserva el flujo actual (sin redirecciones de primera instalación)
- [x] i18n EN+ES y gates frontend (`lint`/`test`/`build`) sin regresiones

## Files to Create
- `frontend/src/api/setupApi.ts`
- `frontend/src/router/setupGuard.spec.ts` (o spec equivalente del guard)

## Files to Modify
- `frontend/src/router/index.ts` — guard de instalación encadenado al existente
- `frontend/src/stores/uiStore.ts` — `isInstalled` / `setupChecked` / `checkSetupStatus`
- `frontend/src/App.vue` — `/setup` exento de `LoginScreen`
- `frontend/src/locales/en.json` / `es.json` — claves del guard

## Related Issues
- #543 (`GET /setup/status`), #519 (guard de rutas y `initSession`), #517 (toggle mock/real), #545 (vista `/setup` destino de la redirección)

## Verification (2026-10-03)

**Implementación:** nuevo `frontend/src/api/setupApi.ts` (`getSetupStatus()` con unwrap del envelope `APIResponse`; en mock no llama a la API real), estado `isInstalled: boolean | null` + `setupChecked` + `checkSetupStatus()` en `stores/uiStore.ts` (una sola llamada HTTP por carga del SPA; si el check falla deja `isInstalled=null` y no bloquea la navegación), guard extraído a `router/setupGuard.ts` y encadenado en `router/index.ts` tras `initSession()` y **antes** del control `meta.roles`, ruta `/setup` → `SetupWizardView.vue` (placeholder con spinner e i18n; lo reemplaza el wizard de #545), exención de `LoginScreen` para `/setup` en `App.vue`, i18n `setup.*` EN+ES.

**Gates frontend (sin regresiones):**
- `npm run lint` → **0 errores** (2 warnings preexistentes `vue/no-mutating-props`)
- `npm test` → **242 passed / 31 ficheros** (baseline 237 + 5 nuevos de `router/setupGuard.spec.ts`)
- `npm run build` → verde (vue-tsc + vite), además build extra con `VITE_USE_MOCK=false` para el smoke

**Smoke live (Chromium/Playwright contra `:19001`, dist reconstruido en modo real, API `:8888`):**
- Stack recién reseteado (sin instalar): `goto /` → URL `/setup`, heading "Tasker Setup" visible y `login-submit` ausente (sin LoginScreen)
- `POST /api/v1/setup/initialize` → 200 (endpoint #543 con `project_name: Review544`)
- `goto /setup` con el sistema instalado → URL `/board` con el shell de la app renderizado
- Post-smoke: reset del stack (proyecto Review544 + políticas + nodo `:User admin` + fila PG creados por el smoke) → `GET /setup/status` final `{"installed": false, "needSetup": true}`

**Decisiones:**
- Guard en módulo propio (`setupGuard.ts`) para poder testearlo aisladamente; se ejecuta antes del check de roles porque un sistema sin instalar no tiene admin ni JWT
- Fallo del check → `isInstalled=null` + toast `setup.statusError` solo en el primer intento (los fallos cacheados no repiten toast); la app nunca queda bloqueada si la API está caída
- Modo mock: el guard se omite por completo y `getSetupStatus()` no se invoca (demo intacta, AC de mock)
- La ruta `/setup` se registra ya en #544 con una vista placeholder mínima porque el AC exige que la raíz caiga en una vista real de `/setup`; #545 la reemplaza por el `SetupWizardView.vue` completo
- En Docker `index.html` inyecta `window.__API_KEY__` (por eso `isAuthenticated` es true y el LoginScreen no aparece en el contenedor); la exención por path en `App.vue` cubre los despliegues sin API key
