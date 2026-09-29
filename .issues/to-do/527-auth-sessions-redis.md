# Issue #527: Auth API & Redis Session Management

## Description

`POST /api/v1/auth/login` valida una API key contra `InMemoryAuthProvider` (fichero) y la rotación de refresh tokens vive en memoria por proceso (#519): no hay estado de sesión persistente ni compartido entre réplicas. La ÉPICA 1 de `notas.md` pide login con credenciales en PostgreSQL, estado de sesión en Redis bajo `session:{user_id}:{session_id}` con TTL, logout que revoca en Redis y refresh que renueva la sesión.

Origen: `notas.md` → ÉPICA 1 · Issue #3 (→ #527).

## Status: TODO

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
- [ ] `POST /api/v1/auth/login` recibe credenciales, valida el hash en PostgreSQL y emite JWT
- [ ] Estado de sesión guardado en Redis bajo `session:{user_id}:{session_id}` con TTL
- [ ] `POST /api/v1/auth/logout` revoca el token/sesión en Redis
- [ ] `POST /api/v1/auth/refresh` renueva el `access_token` usando un `refresh_token` válido, actualizando la sesión
- [ ] Fallback in-memory sin Redis (dev local); tests; gates backend sin regresiones

## Files to Create
- `src/socialseed_tasker/auth/redis_sessions.py`
- `tests/api/test_auth_redis_sessions_unit.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/auth.py` — login PG, sesión Redis, logout/refresh
- `src/socialseed_tasker/infrastructure/web_api/app.py` — wiring del session store
- `pyproject.toml` — `redis`
- `docker-compose.yml` — env/depends de Redis
- `features.md` — §2/§64

## Related Issues
- #519 (OAuth2/JWT actual — base a extender), #526 (users en PostgreSQL), #525 (servicio Redis), #107 (API authentication), #303 (RBAC)
