# Issue #554: Login con usuario y contraseña en el LoginScreen

## Description

El `LoginScreen` solo ofrecía OAuth y un campo de API key: un usuario instalado con
usuario/clave (p. ej. `admin`/`admin` creado en el wizard) no tenía dónde introducir sus
credenciales y "le pide la clave API". El backend ya soporta el login con credenciales
(`POST /auth/login {username,password}` → `_login_with_password`, bcrypt en PostgreSQL,
#526) y el frontend ya tenía `authApi.loginWithCredentials` + `authStore.loginWithCredentials`
(usado por el auto-login del wizard #552) — **solo faltaba la UI**.

Origen: reporte del usuario al abrir el board tras el despliegue de #552/#553.

## Status: DONE (2026-10-06)

## Priority: MEDIUM

## Component
Frontend / LoginScreen

## Type
feat / UX (autenticación)

## Implementation
1. **`LoginScreen.vue`:** nuevo `mode = ref<'credentials' | 'apiKey'>` con **`credentials` por defecto**. Modo credentials: inputs `username` (`autocomplete="username"`) + `password` (`type="password"`, `autocomplete="current-password"`) → `authStore.loginWithCredentials(user.trim(), pass)` → `emit('loggedIn')`. Enlace `login-toggle-apikey` ("Entrar con clave API") conmuta al modo `apiKey` (formulario original con `authStore.login(apiKey)` + master key #552 intacta) y `login-toggle-credentials` conmuta de vuelta. Párrafo superior (`enterCredentials`/`enterApiKey`) y divisor (`orAccount`/`orContinue`) condicionales al modo. Submit deshabilitado si faltan campos (`canSubmit`) o `busy`; errores vía `authStore.error` (`login-error`). OAuth GitHub/Google sin cambios.
2. **i18n (es/en, +6 claves):** `auth.username`, `auth.password`, `auth.enterCredentials`, `auth.orAccount`, `auth.useApiKey`, `auth.useCredentials` — estilo ASCII de la sección `auth` (`Clave` en lugar de `Contraseña`, coherente con "Clave API").
3. **Tests:** nuevo `LoginScreen.spec.ts` (5 tests, mock de `@/api/authApi` al patrón de `authStore.spec`): credentials por defecto, submit deshabilitado hasta completar campos, login con `admin/admin` → `loginWithCredentials` + `emitted('loggedIn')`, conmutador a API key (login con key + vuelta), y error del store visible en rechazo.

## Acceptance Criteria
- [x] Por defecto el LoginScreen muestra usuario y contraseña (no el campo de API key)
- [x] `admin`/`admin` (o cualquier cuenta PG) inicia sesión: submit → `POST /auth/login {username,password}` → sesión y `loggedIn`
- [x] El modo API key (incluida la master key `tasker_sk_live_…` de #552) sigue disponible detrás del enlace de conmutación
- [x] OAuth GitHub/Google intactos; divisor y párrafo superior cambian según el modo
- [x] Submit deshabilitado con campos vacíos o durante `busy`
- [x] Verificación en vivo: `POST /api/v1/auth/login {"username":"admin","password":"admin"}` → **HTTP 200** + token ADMIN (backend sin cambios)
- [x] Gates: `npm run lint` 0 errors/2 warnings preexistentes, `npm test` **301 passed (43 files)** (baseline 296/42, +5 tests/+1 spec), `npm run build` OK (vue-tsc limpio), i18n EN/ES **1690/1690**
- [x] Sin cambios de backend

## Files to Create
- `frontend/src/components/auth/LoginScreen.spec.ts` — 5 tests (modo por defecto, disabled, credentials login, toggle API key/back, error)
- `.issues/done/554-login-usuario-clave-login-screen.md` — este fichero

## Files to Modify
- `frontend/src/components/auth/LoginScreen.vue` — modo credentials por defecto + toggle `apiKey`
- `frontend/src/locales/es.json` / `en.json` — 6 claves `auth.*`
- `features.md` — §64 (filas Login screen, i18n y nueva fila #554)
- `.issues/to-do/INDEX-notas-v6-notifications-mongodb.md` — fila + follow-up #554

## Notes
- **Sin backend nuevo:** el contrato `{username,password}` existía desde #526 y `loginWithCredentials` desde #552 (auto-login del wizard); el fix es 100% UI.
- **Verificación en vivo previa:** curl al `POST /auth/login` con `admin/admin` devolvió 200 con rol ADMIN antes de tocar la UI.
- **`SetupWizardView` fallback intacto:** el wizard muestra la master key y remite al LoginScreen; el modo `apiKey` sigue ahí tras el conmutador.
- **Genérico TS en spec:** `wrapper.find<HTMLButtonElement>(...)` rompía el parser de esbuild del runner → sin genérico (`wrapper.find(...)`).
- **`emitted('loggedIn')` asincrónico:** el emit ocurre en el microtask posterior a `trigger('submit')` → las aserciones usan `vi.waitFor`.

## Related Issues
- #526 (login username/password en backend), #519 (LoginScreen original), #552 (auto-login del wizard + `loginWithCredentials` + master key), #553 (follow-up anterior)
