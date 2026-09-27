# Issue #519: OAuth2 / SSO Authentication & Role-Based Route Protection

## Description

La autenticación se realiza únicamente mediante la validación de una clave de API guardada en `localStorage` o auto-autenticación mock (`authStore` + `LoginScreen`). Se necesita un flujo de inicio de sesión seguro con JWT o proveedor SSO (OAuth2 con GitHub/Google), rotación de refresh tokens y restricción de rutas/acciones según roles heredados del backend.

Origen: `notas.md` → [ISSUE-03] Sistema de Autenticación Completo (OAuth2 / SSO) (→ #519).

## Status: TODO

## Priority: HIGH

## Component
Frontend / Auth / Security

## Type
feat / security

## Implementation
1. **Flujo de login:** extender `LoginScreen.vue` con botones OAuth2 (GitHub/Google, flujo PKCE) además del acceso por API key actual; `authStore` con `login`, `logout`, `refresh`, estado de sesión y usuario/roles persistidos; nuevo `api/authApi.ts` (`/api/v1/auth/*`).
2. **Tokens seguros:** access token corto + refresh token con rotación; interceptor en `client.ts` que ante 401 intenta refresh y reintenta la petición una vez; expiración, logout silencioso y limpieza de estado; preferir memoria en RAM con fallback localStorage documentado.
3. **RBAC de rutas y acciones:** roles reales desde el backend (integrar con roles de organización de #509 y la matriz de #510): guard en `router.beforeEach` para rutas sensibles (`/users`, `/organizations`, `/audit-log`, `/constraints`), items de Sidebar condicionados y `can(action)` en el store para habilitar/deshabilitar acciones (editar, aprobar HITL, kill switch).
4. **Modo demo intacto:** la auto-autenticación mock sigue disponible para demostraciones sin backend; verificar contra `tasker-api` real (:8888).
5. i18n y build.

## Acceptance Criteria
- [ ] Secure login with JWT and/or OAuth2 provider (GitHub/Google), API key fallback preserved
- [ ] Refresh token rotation with automatic retry on 401; session survives reload
- [ ] Routes, sidebar items and actions restricted by backend roles (RBAC); mock demo mode intact
- [ ] Logout clears tokens and store state
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/api/authApi.ts`
- `frontend/src/composables/useAuthGuard.ts` (o guards en el router)

## Files to Modify
- `frontend/src/stores/authStore.ts` — sesión JWT, refresh, roles
- `frontend/src/components/auth/LoginScreen.vue` — botones OAuth2
- `frontend/src/api/client.ts` — interceptor 401 → refresh
- `frontend/src/router/index.ts` — guards por rol
- `frontend/src/components/layout/Sidebar.vue` — items por permisos
- `frontend/src/locales/en.json` / `es.json` — auth/login
- `features.md` — cuando esté done

## Related Issues
- #69 (API Key Authentication), #107 (API Authentication), #122 (Admin Authentication), #155 (Frontend Authentication), #162 (Frontend Authentication Handling), #437 (Fix Auth Mock Mode), #303 (RBAC for CLI & App), #310 (SSO OAuth2 Keycloak Backend), #509 (Multi-Tenancy Org Roles), #510 (Governance RBAC & HITL UI)
