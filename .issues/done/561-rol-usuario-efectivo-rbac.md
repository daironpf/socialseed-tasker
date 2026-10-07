# Issue #561: El rol editado surte efecto real en RBAC (JWT desde la raíz PG)

## Description

El rol del usuario vive en la raíz PG (`users.role`, canónico `ADMIN|DEVELOPER|VIEWER`) y es lo
que RBAC consume: `authenticate_user` lo devuelve (`user_store.py:66`), `issue_tokens` lo firma
en el JWT como claim `role` (`tokens.py:74`) y el middleware de admin lo compara con `ADMIN`.

**Gap**: los tokens en circulación llevan el rol **copiado en el momento del login/refresh**:

- `rotate(refresh)` re-firma los claims **del propio refresh token** (`tokens.py:143-144`) —
  no vuelve a mirar PG.
- `GET /auth/me` responde con los claims del access token (`auth.py:276`).

Resultado: editar el rol en la vista (#560) cambia PG pero **el usuario sigue actuando con el
rol viejo** hasta que cierre sesión manualmente — la funcionalidad "cambiar rol" no está
completa.

## Status: DONE (2026-10-07)

## Priority: MEDIUM

## Component
Backend / Auth

## Type
feat / backend

## Implementation
1. **Revocar las sesiones del usuario al cambiar su rol** (decisión: fuerza re-login con el rol
   nuevo — determinista y testeable, sin refactorizar `rotate`):
   - En `PUT /users/{id}`, cuando `body.role` cambia efectivamente (UPDATE de
     `human_user.role_id` FK → `roles`, #558/#560) y `human_user.password_hash` no está vacío:
     revocar **todas** las sesiones del `sub` = uid PG — borrar las claves Redis
     `session:{user_id}:*` (patrón `redis_sessions.AuthSessionStore`, ¿sweep/scan por prefijo o
     índice por usuario? añadir `delete_all_for_user(user_id)`) y limpiar los refresh `jti`
     activos del sub en `tokens._ACTIVE` (función nueva `revoke_all_for_subject(sub)`).
   - Best-effort: si Redis no está configurado degrada a memoria (patrón existente).
2. **El siguiente refresh con token viejo → 401** (ya no hay `jti` activo ni sesión `sid`) →
   el interceptor del frontend dispara `auth:unauthorized` → pantalla de login limpia (#557) →
   login nuevo emite JWT con el **rol actual de PG**.
3. **`GET /auth/me`**: comprobar que devuelve el rol del token vigente; opcional (si se
   prefiere menos fricción que el logout) en vez de revocar: hacer que el **refresh re-lea
   `role/permissions` de PG por `sub`** al firmar — dejar ambas opciones en la issue y elegir
   **revocación** por defecto (más seguro: un rol degradado no conserva access token vivo más
   de su TTL… nota: el access actual sigue siendo válido hasta expirar — AC lo fija).
4. **Tests** (obligatorios): `tests/api/test_users_api.py` o test de auth —
   `test_role_change_revokes_sessions_and_new_login_has_new_role`: login (admin) → `PUT
   /users/{id}` rol `DEVELOPER` → refresh con el token viejo **401** → login otra vez → claim
   `role == 'DEVELOPER'` y `me` lo refleja; `test_role_change_without_role_field_keeps_sessions`
   (PUT sin `role` no revoca nada).

## Acceptance Criteria
- [x] Cambiar el rol de un usuario con credencial revoca sus sesiones (refresh antiguo → 401)
  — `test_role_change_revokes_sessions_and_new_login_has_new_role` (refresh 401 + access
  viejo también cae en `/auth/me` por la sesión borrada)
- [x] Tras re-login, el JWT y `GET /auth/me` llevan el rol nuevo de PG — mismo test
  (`role == 'DEVELOPER'` en el par nuevo y en `me`)
- [x] Un PUT sin cambio de rol (o de solo perfil) **no** revoca sesiones —
  `test_role_change_without_role_field_keeps_sessions` (solo perfil → 200, rol con el mismo
  valor → 200; el cambio efectivo a `DEVELOPER` del final sí revoca → 401)
- [x] La revocación degrada sin Redis (memoria) sin romper el PUT — backend `memory` en el
  test (sin `TASKER_REDIS_URL`) y PUT responde 200 mientras revoca
- [x] **Tests**: los 2 pytest listados pasan (+2 unitarios: `delete_all_for_user` solo borra
  las sesiones del uid, `revoke_all_for_subject` mata los refresh `jti`)
- [x] Gates backend sin regresiones: `ruff` 1334, `mypy` 1136, `pytest` 1418+3
  (2026-10-07; los números del encabezado eran los del snapshot de la issue)

## Resolution (2026-10-07)
- **Decisión implementada: revocación** (la alternativa de `rotate()` releyendo PG queda
  documentada en Notes y no elegida). Hook en `PUT /users/{id}`: si `body.role` cambia
  efectivamente (`profile['role']` pre-update ≠ `role_id`) **y** `human_user.password_hash`
  no está vacío (`PostgresUserStore.has_password`), `_revoke_user_sessions` ejecuta
  `tokens.revoke_all_for_subject(uid)` + `AuthSessionStore.delete_all_for_user(uid)`
  (SCAN `session:{uid}:*` en Redis / sweep por prefijo en memoria), todo en try/except
  best-effort para no romper el PUT ya commitado.
- Access tokens con `sid` mueren de inmediato (el middleware y `/auth/me` consultan la
  sesión), no solo al expirar — más estricto que el AC, anotado en el test.
- Sin credencial (#563 pendiente, `password_hash=''`) no hay sesiones de password que
  revocar: el hook hace `return` sin tocar nada.

## Files to Create
- (ninguno)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (hook de revocación en PUT)
- `src/socialseed_tasker/auth/tokens.py` (`revoke_all_for_subject`)
- `src/socialseed_tasker/auth/redis_sessions.py` (`delete_all_for_user`)
- `src/socialseed_tasker/auth/user_store.py` (`has_password`)
- `tests/fakes/fake_pg_users.py` (handler del SELECT de credencial)
- `tests/api/test_users_api.py` (los 2 tests obligatorios; las llamadas directas pasan `request`)
- `tests/api/test_auth_redis_sessions_unit.py` (2 unitarios de revocación)

## Notes
- Alternativa no elegida (documentarla): `rotate()` re-firmando desde PG → cambio de rol sin
  logout; requiere que el router de refresh pase el usuario leído a `rotate` (refactor de
  firma pura). La revocación es la elegida por seguridad + testabilidad.
- El id PG es el `sub` — la revocación se indexa por eso (coherencia con "PG indexa todo").

## Related Issues
- #560 (editar rol desde la vista), #558 (raíz PG), #527/#519 (JWT/refresh), #557 (login limpio
  al expirar la sesión)
