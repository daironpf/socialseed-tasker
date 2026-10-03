# Issue #544: Navigation guard de instalación y estado `isInstalled` en el frontend

## Description

El frontend en Vue 3 debe interceptar la navegación de las rutas principales (`/`, `/kanban`, `/graph`, …) para redirigir forzosamente a la vista `/setup` si el sistema no ha completado la instalación inicial (servidor `GET /api/v1/setup/status` de #543), y evitar entrar al wizard cuando el sistema ya está instalado.

Contexto real del repo: `router.beforeEach` ya existe y encadena `authStore.initSession()` + control `meta.roles` (#519); el overlay `LoginScreen` cubre la app cuando no hay sesión (`App.vue`), por lo que `/setup` debe quedar exento de login; y en **modo mock** (`isMockMode()`, #517) la demo autoautenticada no debe quedar bloqueada por un guard de primera instalación.

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #3 (→ #544).

## Status: TODO

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
- [ ] Abrir la raíz de la aplicación en un navegador con el sistema nuevo redirige inmediatamente a `http://localhost:<FRONTEND_PORT>/setup`
- [ ] Con `installed === true`, navegar a `/setup` redirige a `/board`
- [ ] `isInstalled` vive en `uiStore` y la consulta se cachea (sin llamadas redundantes por navegación)
- [ ] `/setup` es accesible sin iniciar sesión (no bloqueado por `LoginScreen` ni `meta.roles`)
- [ ] El modo mock conserva el flujo actual (sin redirecciones de primera instalación)
- [ ] i18n EN+ES y gates frontend (`lint`/`test`/`build`) sin regresiones

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
