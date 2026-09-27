# Issue #519: OAuth2 / SSO Authentication & Role-Based Route Protection

## Description

La autenticación se realiza únicamente mediante la validación de una clave de API guardada en `localStorage` o auto-autenticación mock (`authStore` + `LoginScreen`). Se necesita un flujo de inicio de sesión seguro con JWT o proveedor SSO (OAuth2 con GitHub/Google), rotación de refresh tokens y restricción de rutas/acciones según roles heredados del backend.

Origen: `notas.md` → [ISSUE-03] Sistema de Autenticación Completo (OAuth2 / SSO) (→ #519).

## Status: DONE

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
- [x] Secure login with JWT and/or OAuth2 provider (GitHub/Google), API key fallback preserved
- [x] Refresh token rotation with automatic retry on 401; session survives reload
- [x] Routes, sidebar items and actions restricted by backend roles (RBAC); mock demo mode intact
- [x] Logout clears tokens and store state
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

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

## Resolution

Implemented 2026-09-27:

- **JWT (stdlib, sin dependencias nuevas):** `src/.../auth/tokens.py` — HS256 con `hmac`/`hashlib`/`base64`; access 900s + refresh 604800s (env `TASKER_JWT_SECRET`/`TASKER_JWT_ACCESS_TTL`/`TASKER_JWT_REFRESH_TTL`); refresh carries `jti` registrado en un conjunto activo in-memory: la rotación descarta el jti viejo y el reuse de un refresh ya rotado revoca todos los jtis del subject (reuse detection → re-login).
- **Endpoints** `src/.../routers/auth.py` bajo `/api/v1/auth/`: `POST login` (API key → JWT + user con rol derivado de permisos: `admin`→ADMIN, `create/delete:issue`→DEVELOPER, resto VIEWER — reutiliza `InMemoryAuthProvider`/`auth/users.json`), `POST refresh` (rotación), `POST logout` (revoca), `GET me`, OAuth2 GitHub/Google con PKCE (`authorize` con state+challenge TTL 600s → `callback` intercambia code por perfil y redirige a `TASKER_FRONTEND_URL/auth/oauth-callback?code=` one-time 60s → `POST exchange`); sin `GITHUB_*`/`GOOGLE_*` devuelve 403 `oauth_not_configured:{provider}`.
- **Middleware** (`app.py`): exime `/api/v1/auth/*`; mantiene `X-API-Key` intacto y valida como JWT alternativo cualquier `Authorization: Bearer` que no sea la API key → la sesión del frontend pasa sin romper el flujo CLI.
- **Frontend:** `api/authSession.ts` (holder sin ciclos: access en RAM, refresh en localStorage, auto-refresh 60s antes de expirar), `api/authApi.ts` (cliente axios propio con refresh single-flight y `restoreSession` al arrancar), `stores/authStore.ts` (rewrite: `initSession` idempotente, `login`/`loginOAuth`/`completeOAuth`/`logout`, `can(action)`→permiso backend, `hasRole`/`rolesAllowed` con rango ADMIN≥DEVELOPER≥VIEWER; **mock siempre autoriza** → demo intacta), `client.ts` (request `Bearer` + response 401→refresh→retry 1×→si falla `auth:unauthorized` limpia sesión), `composables/useAuthGuard.ts`, guards en `router.beforeEach` con `meta.roles` (`/users`, `/organization`, `/audit-log`, `/constraints`) + redirect `/board` + toast, Sidebar filtrado por `canRoute`, acciones gated (IssueCard kill → `issue.kill`; HITL approve/modify/reject → `hitl.approve`; IssueDetailView selects → `issue.edit`), `LoginScreen` con botones GitHub/Google + error traducido, nueva vista `AuthCallbackView` (ruta `/auth/oauth-callback`), `UserMenu` con username/rol reales y logout que revoca en backend.
- **i18n:** `auth.{github,google,orContinue,invalidKey,loginFailed,oauthError,oauthNotConfigured,forbidden}` EN/ES.
- **Verificación:** backend `ruff`+`mypy` limpios en los ficheros nuevos; smoke `TestClient` 19/19 (middleware 401/200, login admin/viewer, Bearer JWT, `/auth/me`, rotación, reuse detection, logout, tamper, oauth 403, health); frontend `npm test` 91/91 (10 nuevos en `authStore.spec.ts`), `npm run lint` 0 errores, `npm run build` verde, `npm run test:e2e` 8/8.
