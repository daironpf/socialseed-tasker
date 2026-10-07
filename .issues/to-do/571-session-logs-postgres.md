# Issue #571: Log de sesiones en PostgreSQL (`session_logs`) — escritura en login y `last_login` derivado

## Description

Con el esquema normalizado de #558 existe la tabla **`session_logs`**
(`id, user_id→users CASCADE, event login|logout, created_at, ip, user_agent` + índice
`(user_id, created_at DESC)`), pero está vacía: nadie escribe en ella y `GET /users` no tiene
qué derivar.

Situación actual:

- La vista pinta `last_active` desde `last_login` de la respuesta de `/users` — con el esquema
  normalizado **`last_login` no es columna**: se **deriva** de
  `MAX(session_logs.created_at) WHERE event='login'`.
- Existe `POST /users/{user_id}/last-login` (`routers/user.py`) pero **nadie lo llama** —
  endpoint huérfano del maquetado.
- Equivalente mock: `mockApi.login` actualiza `users.json.last_active`.

Decisión: **en el login con credenciales** (`POST /auth/login`, lookup en PG por username/email
→ uid) se inserta la fila `session_logs(event='login', ip, user_agent)`; la auditoría de
sesiones queda durable (antes: solo `last_login` congelado). El refresh/oaut no genera fila
(solo arranque de sesión real) — logout explícito (`POST /auth/logout` si existe, o
`revoke_all_for_subject`) puede registrar `event='logout'` cuando la sesión se revoca (#561).

Origen: restricción del usuario "una tabla para los logs de sesión" del modelo normalizado.

## Status: TODO

## Priority: LOW

## Component
Backend / Auth + Data (PG)

## Type
feat / backend

## Implementation
1. **Escritura en login**: en `POST /auth/login` tras `authenticate_user` exitoso →
   `INSERT INTO session_logs (user_id, event, ip, user_agent) VALUES (%s, 'login', %s, %s)`
   (patrón del store; ip/user-agent desde headers `X-Forwarded-For`/`User-Agent` si están,
   `NULL` si no). **Best-effort**: si la inserción falla, el login igualmente proceeds (log +
   continuar — la credencial es la fuente de verdad).
2. **`last_login` derivado en `GET /users`**: el JOIN de #558 usa
   `(SELECT max(created_at) FROM session_logs sl WHERE sl.user_id = u.id AND sl.event='login')`
   (o subquery lateral) — verificar que `normalizeBackendUser` (`last_login ?? last_active`)
   preserva el ISO y la tarjeta lo pinta.
3. **`event='logout'`** en revocaciones: `revoke_all_for_subject` (#561) inserta
   `event='logout'` best-effort (si #561 ya está cerrada, hacerlo aquí reutilizando su hook;
   si #561 va después, dejar el hook preparado y solo login en este issue — orden recomendado:
   #561 antes que #571).
4. **Retirar el endpoint huérfano** `POST /users/{user_id}/last-login` (nadie lo llama; la
   fuente de verdad es el login). Test de 404/405.
5. **Tests** (obligatorios): `tests/api/test_auth*.py` o `test_users_api.py`:
   - `test_login_writes_session_log` — login → fila `session_logs(event='login')` con
     `user_id` = uid PG e `ip` capturada.
   - `test_get_users_last_login_derived_from_session_logs` — sembrar sesión + GET →
     `last_login` refleja el máximo.
   - `test_login_succeeds_if_session_log_insert_fails` (store fake que lanza → 200 igual).
   - `test_last_login_endpoint_removed` (404/405).

## Acceptance Criteria
- [ ] Cada login con credenciales inserta `session_logs(event='login')` con uid PG, ip y
      user-agent (o NULL)
- [ ] `GET /users.last_login` se **deriva** de `session_logs` (sin columna `last_login` en
      `users`/`human_user`)
- [ ] Un fallo al escribir el log no rompe el login (best-effort + log)
- [ ] El endpoint huérfano `POST /users/{id}/last-login` queda retirado
- [ ] Si #561 está hecha: las revocaciones registran `event='logout'`
- [ ] **Tests**: los pytest listados pasan
- [ ] Gates backend sin regresiones: `ruff` 1011, `mypy` 1153, `pytest` 1331+3

## Files to Create
- (ninguno)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/auth.py` (insert en login)
- `src/socialseed_tasker/auth/user_store.py` (`record_session_event` + subquery de
  `last_login` en los GET)
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (retirar endpoint huérfano)
- `src/socialseed_tasker/auth/tokens.py` (hook `logout` si #561 ya cerró)
- `tests/api/test_users_api.py` / `tests/api/test_auth_sessions.py`

## Notes
- `session_logs` crece por login — añadir limpieza opcional (retención N días) como tarea de
  mantenimiento futura, no en este issue.
- `last_active` del mock es el campo que la vista pinta; no renombrar el front (maqueta
  intacta).
- Los logs de **ejecución** de agentes (`agent_runs`/`agent_run_logs`) son otra cosa → **#574**;
  aquí solo sesiones de usuario.

## Related Issues
- #558 (DDL de `session_logs` + derivación en `GET /users`), #561 (revocación → logout),
  #527/#519 (login credentials), #574 (runs de agentes, aparte)
