# Issue #552: Onboarding de primera entrada tras instalar (2 notificaciones + modo real + auto-login)

## Description

Al entrar por primera vez al dashboard después de instalar, el usuario veía las 5 notificaciones HITL de la demo mock en lugar del onboarding (bienvenida + "ve a Usuarios a definir tu agente").

Diagnóstico confirmado (3 causas encadenadas):

1. **Modo mock por defecto**: `client.ts` resuelve `VITE_USE_MOCK ?? 'true'` y ningún Dockerfile/compose fija `VITE_USE_MOCK=false` → un navegador nuevo (sin `socialseed-api-mode` en localStorage) entra en mock → `setupGuard.ts` hace `if (isMockMode()) return true` y omite `/setup`.
2. **Las 5 HITL vienen de la demo**: en mock, `AppHeader.onMounted` → `hitlStore.fetchRequests()` → `MOCK_REQUESTS` tiene exactamente 5 pendientes → `ensureHitlNotifications` las inyecta. En modo real `requests` queda `[]` (nunca hay HITL).
3. **La welcome no se ve nunca**: solo se inserta en `POST /setup/initialize` (no en instalación CLI) y solo se lee con sesión; tras el wizard no había auto-login y `isAuthenticated` estaba siempre en `true` por el hack `!!API_KEY` (`window.__API_KEY__='test-token'`, que ni siquiera valida en `/auth/login`) → `startRealtime()`/`fetchNotifications` no corrían y ni siquiera se mostraba el LoginScreen.

Decisiones de producto acordadas: **dos** notificaciones de onboarding (amplía el AC de `notas.md` #3), **probe al arrancar** para forzar modo real en navegador nuevo, y **auto-login tras el wizard** + quitar el hack de API key.

Origen: `notas.md` — Sistema de Notificaciones Real en MongoDB → Issue #3 (extendido → #552).

## Status: DONE (2026-10-06)

## Priority: HIGH

## Component
Backend / Onboarding / Setup + Frontend / Auth / API mode

## Type
feat / integration (bug fix de primera entrada)

## Implementation
1. **Segunda notificación (backend):** `setup.py` — `_insert_welcome_notification` ahora siembra un par: la bienvenida literal de `notas.md` y *"Define tus agentes en Usuarios"* (mismo `WELCOME`/`INFO`/`channel=system`/`requires_action`/`link_to: "/users"`, para compartir la categoría frontend `welcome` sin tocar el enum). Idempotencia cambiada de `(user_id, type)` a **por título**: `list_for_user(admin, type=WELCOME, limit=50)` y solo inserta los títulos que falten (un rerun parcial inserta solo lo ausente).
2. **Master key como sesión (backend):** nuevo `setup.resolve_master_key(state) -> (key, admin_username)` (copia en `app.state` con fallback perezoso a la secrets store, ahora también cacheando el `adminUsername` guardado en la metadata por `_persist_master_key`); el middleware de `app.py` y la nueva rama de `_login_with_api_key` (pasa a recibir `request`) lo comparten → `POST /auth/login {api_key: tasker_sk_live_…}` devuelve sesión **ADMIN** del admin instalado.
3. **Probe de modo real (frontend):** nuevo `api/modeBootstrap.ts` — `resolveInitialApiMode()` invocado en `router.beforeEach` **antes** de `initSession()`: sin modo guardado y en mock → `fetch(GET {API_URL}/health)` con timeout 2.5s → `ok` ⇒ `setApiMode('real')` (persistido); error/`!ok` ⇒ mock sin persistir (reintenta en la próxima carga); elección explícita o modo ya real ⇒ sin probe. Memoizado por carga (`resetApiModeProbe()` para tests). Clave de storage exportada como `API_MODE_STORAGE_KEY`.
4. **Auto-login tras el wizard (frontend):** nuevo `authApi.loginWithCredentials(user, pass)` + `authStore.loginWithCredentials` (no persiste API key legacy); en `SetupWizardView.submit()` éxito → login best-effort con las credenciales del formulario (fallback `admin`/`admin` igual que el backend, error limpiado en catch) antes de mostrar el panel de credenciales → `/board` monta con sesión y el watcher de `notificationsStore` hidrata el par de onboarding.
5. **`isAuthenticated` sin hack (frontend):** se elimina `|| !!API_KEY` — una API key en `window` no es sesión; sin sesión real se muestra el LoginScreen (que ahora acepta la master key vía el punto 2).

## Acceptance Criteria
- [x] Tras instalar vía `/setup`, `notifications` contiene exactamente las 2 notificaciones de onboarding para el admin (payload literal), sin duplicados en un rerun y con inserción parcial correcta si solo existe una
- [x] El primer `GET /api/v1/notifications` con sesión del admin incluye ambos mensajes
- [x] Mongo caído/no configurado no rompe `POST /setup/initialize`
- [x] `POST /auth/login {api_key}` con la master key devuelve sesión ADMIN (y sigue tras un reinicio del API vía metadata `adminUsername`); clave errónea → 401
- [x] Navegador nuevo con backend accesible ⇒ probe → modo real persistido; sin backend ⇒ mock sin persistir; elección explícita respetada; probe único por carga
- [x] El wizard deja la sesión del admin iniciada (y degrada al LoginScreen si el login falla)
- [x] Gates backend sin regresiones: `ruff check src` 1011 = baseline, `mypy src` 1152 ≤ baseline 1153, `pytest` 1329 passed + 3 failed preexistentes + 27 skipped (1325 baseline + 4 nuevos)
- [x] Gates frontend sin regresiones: `npm run lint` 0 errors/2 warnings preexistentes, `npm test` 291 passed (41 files, +9), `npm run build` OK, i18n EN/ES 1683/1683 claves

## Files to Create
- `frontend/src/api/modeBootstrap.ts` — probe de modo real al arrancar
- `frontend/src/api/modeBootstrap.spec.ts` — 6 tests del probe

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/setup.py` — par de notificaciones + `resolve_master_key` + metadata `adminUsername`
- `src/socialseed_tasker/infrastructure/web_api/routers/auth.py` — `_login_with_api_key` acepta la master key
- `src/socialseed_tasker/infrastructure/web_api/app.py` — middleware reutiliza `resolve_master_key`
- `tests/api/test_setup_endpoints.py` — tests del par, idempotencia parcial y login por master key
- `frontend/src/api/client.ts` — exporta `API_MODE_STORAGE_KEY`
- `frontend/src/api/authApi.ts` — `loginWithCredentials`
- `frontend/src/stores/authStore.ts` — `loginWithCredentials`, `isAuthenticated` sin `!!API_KEY`
- `frontend/src/stores/authStore.spec.ts` — +2 tests
- `frontend/src/router/index.ts` — `resolveInitialApiMode()` antes de `initSession()`
- `frontend/src/views/SetupWizardView.vue` — auto-login best-effort en `submit()`
- `frontend/src/views/SetupWizardView.spec.ts` — mock de authApi + aserción de auto-login + fallback
- `notas.md` — Issue #3 extendido a dos notificaciones + AC de primera entrada
- `features.md` — §21/§62/§69 actualizados

## Notes
- **Ambas notificaciones `type=WELCOME`:** evita tocar `NotificationType`/`FRONTEND_CATEGORIES` y el union type del frontend; la idempotencia pasa a ser por título, que es la única forma de distinguirlas. Alternativa descartada (más coste): enum nuevo `AGENT_SETUP`.
- **Probe contra `/health`:** es de los endpoints exentos del middleware API key (`/health`, `/api/v1/health`, `/docs`, `/openapi.json`, `/redoc`, `/api/v1/auth/*`, `/api/v1/setup/*`), así el probe no depende de que `window.__API_KEY__` coincida con `TASKER_API_KEY`. Se exige `response.ok` (200): un 502 del proxy con el API caído no activa el modo real.
- **Instalación CLI/por arranque del contenedor:** sigue sin sembrar el par de onboarding (solo `POST /setup/initialize`), igual que antes con la bienvenida; fuera de alcance acordado. El probe + LoginScreen cubren la visibilidad cuando el backend ya está instalado por CLI (credenciales: master key o `admintoken123` de `auth/users.json`).
- **Carrera de sesión:** `initSession` está memoizado (`initPromise`), por lo que el auto-login del wizard no puede ser sobrescrito por un `restoreSession` posterior en la misma carga.
- **Demo mock intacta:** las 5 HITL siguen siendo el data fixture intencional cuando no hay backend; el fix no toca `MOCK_REQUESTS` ni `ensureHitlNotifications`.

## Related Issues
- #543/#545/#546 (initialize + wizard + master key), #547/#548 (modelo + REST), #549 (bienvenida), #550/#551 (stream + store real), #544 (guard que complementa el probe)
