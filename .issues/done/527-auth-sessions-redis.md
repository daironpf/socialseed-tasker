# Issue #527: Auth API & Redis Session Management

## Description

`POST /api/v1/auth/login` valida una API key contra `InMemoryAuthProvider` (fichero) y la rotación de refresh tokens vive en memoria por proceso (#519): no hay estado de sesión persistente ni compartido entre réplicas. La ÉPICA 1 de `notas.md` pide login con credenciales en PostgreSQL, estado de sesión en Redis bajo `session:{user_id}:{session_id}` con TTL, logout que revoca en Redis y refresh que renueva la sesión.

Origen: `notas.md` → ÉPICA 1 · Issue #3 (→ #527).

## Status: DONE (2026-09-30)

## Priority: HIGH

## Component
Backend / Auth / Sessions / Redis

## Type
feat / security

## Implementation
1. **Login contra PostgreSQL:** `POST /api/v1/auth/login` acepta `username` + `password`, normaliza el username (#526) y valida el hash bcrypt almacenado; mantiene compatibilidad con la API key (fallback) y con OAuth2 (#519).
2. **Sesión en Redis:** al emitir el JWT se persiste `session:{user_id}:{session_id}` con TTL = expiración del refresh token (jti, roles, timestamps, user-agent); `redis-py` con fallback in-memory si no hay `TASKER_REDIS_URL`.
3. **Logout que revoca:** `POST /auth/logout` elimina la sesión en Redis además de revocar el jti actual.
4. **Refresh que renueva:** `POST /auth/refresh` valida el refresh, rota el jti (reuse detection de #519) y actualiza/crea la clave de sesión en Redis con TTL nuevo.
5. **Middleware:** rechaza tokens cuya sesión esté revocada (consulta Redis; sin Redis mantiene la validación de firma actual).

## Acceptance Criteria
- [x] `POST /api/v1/auth/login` recibe credenciales, valida el hash en PostgreSQL y emite JWT
- [x] Estado de sesión guardado en Redis bajo `session:{user_id}:{session_id}` con TTL
- [x] `POST /api/v1/auth/logout` revoca el token/sesión en Redis
- [x] `POST /api/v1/auth/refresh` renueva el `access_token` usando un `refresh_token` válido, actualizando la sesión
- [x] Fallback in-memory sin Redis (dev local); tests; gates backend sin regresiones

## Verification (2026-09-30)
- **Login PG:** `authenticate_user()` en `auth/user_store.py` (SELECT por `username_normalized` + `verify_password` bcrypt; desconocido/mal password → `None` → 401, error de conexión/SQL → 503 `Auth store unavailable`); roles PG → permisos (`lead-developer`/`developer`/`ai-agent` → dev, `*admin*` → ADMIN, resto VIEWER); `POST /auth/login` acepta `{username, password}` o `{api_key}` (400 si ninguno) y la ruta API key sigue usando `InMemoryAuthProvider`.
- **Sesión Redis:** `AuthSessionStore` en `auth/redis_sessions.py`, clave `session:{user_id}:{session_id}` con JSON (`session_id`, `user_id`, `username`, `role`, `permissions`, `access_jti`, `refresh_jti`, `user_agent`, `created_at`, `updated_at`) y TTL = `REFRESH_TTL` (604800s); `redis-py` con `decode_responses`, degradación a dict in-process (lock + expiración) si no hay `TASKER_REDIS_URL` o si Redis falla en runtime; wiring `app.state.auth_sessions` + log `auth session store backend: redis`.
- **Claim `sid`:** `tokens.issue_tokens(user, session_id)` y `tokens.rotate(refresh, session_id)` firman `sid` en access y refresh (sin parámetro → sin `sid`, tokens antiguos siguen funcionando).
- **Logout:** borra la sesión vía `refresh_token` presentado (y revoca su jti) o vía el `Authorization: Bearer` si no hay refresh; `GET /auth/me` → 401 `Session revoked` y middleware `_verify_jwt` → 401 `UNAUTHORIZED` cuando el `sid` ya no existe.
- **Refresh:** consulta la sesión ANTES de rotar (si falta → 401 `Session revoked` sin consumir el jti), rota el jti (reuse detection de #519) y re-graba la sesión conservando `created_at` y con TTL nuevo; refresh sin `sid` (token legado) crea una sesión nueva; `POST /auth/exchange` (OAuth) también crea sesión.
- **Smoke real (compose, 22/22):** login `Manolo/manolo` → 200 (`user=manolo role=DEVELOPER`), clave `session:550e8400-...:<sid>` en Redis con TTL 604799; `me` y `GET /api/v1/labels` con token vivo → 200; logout → clave borrada de Redis, `me` → 401 `Session revoked`, `labels` → 401 `UNAUTHORIZED` (middleware), refresh → 401 `Session revoked`; password incorrecto 401, usuario inexistente 401, sin credenciales 400, API key inválida 401; relogin → refresh 200 con rotación de `refresh_jti` en Redis y TTL renovado; reutilizar el refresh viejo → 401.
- **Tests:** `tests/api/test_auth_redis_sessions_unit.py` (23 tests): store (clave/TTL/roundtrip/fallback sin Redis), claims `sid` en issue/rotate, `authenticate_user` sin red, login PG (200/401/400/503/ADMIN), API key, ciclo de vida (`me`/logout/refresh/reuse/middleware con sesión revocada).
- **Gates:** `ruff` = 1011 (baseline), `mypy` = 1155/133 (baseline), `pytest` = 1141 passed (+23) / 27 skipped / 3 failed preexistentes (`test_delivery_retries`, 2× `test_tasks_unit`).

## Files to Create
- `src/socialseed_tasker/auth/redis_sessions.py` — `AuthSessionStore` (Redis + fallback in-memory)
- `tests/api/test_auth_redis_sessions_unit.py`

## Files to Modify
- `src/socialseed_tasker/auth/tokens.py` — claim `sid` opcional en `_access_claims`/`issue_tokens`/`rotate`
- `src/socialseed_tasker/auth/user_store.py` — `authenticate_user()` (SELECT + bcrypt)
- `src/socialseed_tasker/infrastructure/web_api/routers/auth.py` — login PG/api-key, persistencia de sesión en login/refresh/exchange, logout/`me` con revocación
- `src/socialseed_tasker/infrastructure/web_api/app.py` — wiring `app.state.auth_sessions` + chequeo de sesión en `_verify_jwt`
- `pyproject.toml` — `redis` (ya resuelto en #525)
- `docker-compose.yml` — env/depends de Redis (ya resuelto en #525)
- `features.md` — §2/§64

## Related Issues
- #519 (OAuth2/JWT actual — base extendida con `sid`), #526 (users en PostgreSQL), #525 (servicio Redis), #107 (API authentication), #303 (RBAC), #533 (health con Redis/Postgres)
