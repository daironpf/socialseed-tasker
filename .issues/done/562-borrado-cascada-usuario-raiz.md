# Issue #562: Borrado raíz en cascada — eliminar usuario borra su credencial PG y sus datos indexados

## Description

`DELETE /users/{id}` (#556) solo borra el nodo de **proyección** (Neo4j) y cuenta humanos en
Neo4j. Con la restricción **PG = raíz** esto deja dos agujeros:

1. **La fila PG (credencial) queda viva** → un usuario "eliminado" desde la vista **sigue
   pudiendo loguearse** con su password (autenticación lee PG, no Neo4j).
2. El guard del último humano cuenta `repo.list_users(limit=2)` de Neo4j, no los humanos de la
   raíz — debe contar en PG (`user_type = 'human'`, incluye el `admin` sembrado).
3. Los datos indexados por el id PG en otras bases (proyección `(:User)`, refresh `jti`,
   sesiones Redis, `notifications.user_id` en Mongo) quedan huérfanos.

Mock de referencia: `mockApi.deleteUser` elimina la entidad de la colección y desaparece de la
lista; en real el equivalente es que desaparezca de **la raíz** y de todo lo indexado por su id.

## Status: DONE

## Priority: HIGH

## Component
Backend / Auth + Data (PG raíz + cascada best-effort)

## Type
feat / backend

## Implementation
1. **Guard en la raíz**: en `delete_user`, contar humanos en **PG**
   (`SELECT count(*) FROM users WHERE user_type = 'human'`) → `<= 1` ⇒ **409
   `Cannot delete the last user`** (conservar código 409 y detail de #556; cambiar la fuente
   del conteo a PG).
2. **DELETE en PG**: `DELETE FROM users WHERE id = %s RETURNING id` → sin fila ⇒ **404**
   (antes `delete_user` no comprobaba existencia); **`human_user`, `agents_user`,
   `user_skills` y `session_logs` caen por sus FK `ON DELETE CASCADE`** (esquema #558/#564).
3. **Revoke de sesiones del sub** (reutilizar `revoke_all_for_subject` de #561): refresh `jti`s
   activos + sesiones Redis del id PG — un usuario borrado no conserva sesión abierta.
4. **Cascada best-effort sobre datos indexados por el id PG** (log + no romper si falta un
   servicio, patrón `ChatStoreError`):
   - Neo4j: borrar el nodo de proyección `(:User {id})` (y sus relaciones de grafo).
   - Mongo: borrar `notifications` con `user_id = id` (patrón de wipe de #549).
   - Sin database url / sin Mongo → log y continuar (el borrado de la raíz ya es el
     efecto garantizado).
5. **Frontend**: `deleteUser`/`deleteAgent` en `UsersView` muestran el `detail` del backend en
   el toast si existe (clave `common.error` como fallback) — el 409 del guard ya tiene
   `users.lastUserGuard` en el disabled del botón.
6. **Tests** (obligatorios): ampliar `tests/api/test_users_api.py`:
   - `test_delete_user_removes_postgres_credential` — tras DELETE, `authenticate_user` con sus
     credenciales devuelve `None` y la fila no existe (PG real o fake con las mismas
     aserciones).
   - `test_delete_last_human_counts_postgres_and_returns_409` (ahora con humanos en PG).
   - `test_delete_user_revokes_sessions` — refresh previo al borrado → 401.
   - `test_delete_user_cleans_projections` — driver Mongo/Neo4j fake: se invocan las limpiezas
     y los fallos no rompen el 200.
   - Frontend: spec del toast con `detail` (si se añade lógica en `UsersView.spec.ts`).

## Resolution

**Resuelto 2026-10-08.**

- **Guard + 404 en la raíz**: `delete_user` pasa a `async def (user_id, request, driver)` y
  primero lee el perfil con `PgUserRepository.get_user` → sin fila ⇒ **404 `User not found`**;
  si `type == 'human'` y `PgUserRepository.count_humans() <= 1` ⇒ **409 `Cannot delete the
  last user`** (fuente PG: `SELECT count(*) FROM users WHERE user_type = 'human'`, incluye
  el admin sembrado; los agentes no disparan el guard — nota del issue).
- **DELETE PG autoritativo** (decisión documentada): `delete_user_row` (rowcount) → sin fila
  ⇒ 404 (carrera), excepción ⇒ **500 `PostgreSQL user delete failed`** —antes un fallo PG se
  tragaba y devolvía 200—; sin `TASKER_DATABASE_URL` ⇒ **503** (el issue era ambiguo con
  «log y continuar»; se eligió 503 por consistencia con el resto de `/users`). `human_user`,
  `agents_user`, `user_skills` y `session_logs` caen por las FK `ON DELETE CASCADE` (#558).
- **Revocación incondicional** (reutiliza #561): `tokens.revoke_all_for_subject(uid)` +
  `AuthSessionStore.delete_all_for_user(uid)` en try/except best-effort (la fila raíz ya no
  existe); el access con `sid` muere de inmediato (middleware/`me` consultan la sesión).
- **Cascada best-effort sobre datos indexados**: Neo4j `UserRepository.delete_user` solo si
  hay driver (sin driver ⇒ log, ya no 503) y Mongo `NotificationMongoRepository().clear_all(
  uid)` (async); ambos dentro de try/except que degradan a log sin romper el 200.
  `notifications` globales no se tocan (`clear_all` filtra por `user_id`).
- **Frontend**: `usersStore.deleteUser` re-lanza el error (`Promise<void>`, patrón #559/#560),
  `usersApi.deleteUser` mutea el toast genérico (`suppressErrorToast`, como create/update) y
  `deleteUser`/`deleteAgent` en `UsersView` muestran ``Error: {detail}`` (fallback
  `common.error`); `closeEditAgent()` solo se cierra en éxito. El disabled del botón sigue
  usando `users.lastUserGuard`.
- **Tests** (+4 netos; los 5 call sites directos pasaron a `async` + `request=MagicMock()`):
  los 4 obligatorios — `test_delete_user_removes_postgres_credential` (bcrypt real: `authenticate_user`
  antes → 200 → `None` y fila borrada), `test_delete_last_human_counts_postgres_and_returns_409`
  (409 y nada borrado), `test_delete_user_revokes_sessions` (login HTTP → DELETE → refresh
  401 + access 401 + re-login 401) y `test_delete_user_cleans_projections` (fallos Neo4j+Mongo
  registrados y el 200 no se rompe) — más `test_delete_agent_skips_the_human_guard`,
  `test_delete_not_found_404`, `test_delete_fails_when_postgresql_fails` (500) y
  `test_delete_without_database_url_returns_503`, que sustituyen a los 3 tests legacy con la
  semántica Neo4j-first. Fake `FakePgCursor`: handler `select count(*) from users where
  user_type`; helper `_install_delete` = lectura de perfil compuesta + guard/DELETE con SQL
  real sobre el cursor; `_read` del fake ahora respeta `user_type`. Frontend: 2 specs nuevas
  en `UsersView.spec.ts` (detail en toast + baja de tarjeta en éxito).
- **Gates** (2026-10-08): `ruff check .` **1334** / `mypy src` **1136** / `pytest` **1422
  passed** + 3 preexistentes + 27 skipped; frontend `lint` 0/2 / `test` **317 (45)** /
  `build` OK / i18n **1696/1696**.

## Acceptance Criteria
- [x] Tras `DELETE /users/{id}`, la fila PG no existe y **ese usuario no puede iniciar sesión**
- [x] El guard de último humano cuenta en **PG** y responde 409 sin borrar nada
- [x] Las sesiones/refresh del usuario borrado quedan revocadas (refresh → 401)
- [x] Proyección Neo4j y `notifications` de Mongo del id PG se limpian best-effort (degradan a
      log sin servicios)
- [x] 404 al borrar un id inexistente
- [x] **Tests**: los pytest listados + frontend pasan
- [x] Gates backend sin regresiones: `ruff` 1334 / `mypy` 1136 / `pytest` 1422+3
      preexistentes; frontend `lint` 0/2 / `test` 317 / `build` OK

## Files to Create
- (ninguno)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (`delete_user`)
- `src/socialseed_tasker/auth/tokens.py` / `redis_sessions.py` (reutilizar revocación #561)
- `src/socialseed_tasker/infrastructure/neo4j_user_repository.py` (borrado de proyección)
- `frontend/src/views/UsersView.vue` (toast con detail)
- `tests/api/test_users_api.py`

## Notes
- Orden recomendado en el lote: **#561 antes que #562** (comparten `revoke_all_for_subject`).
- No borrar `notifications` del "global/system" (`user_id != id`).
- Los agentes (`type='agent'`) no están sujetos al guard de humanos (ya lo era así en #556).

## Related Issues
- #556 (guard 409 original), #558 (raíz PG), #561 (revocación de sesiones),
   #564 (`agents_user` con `ON DELETE CASCADE`), #547/#549 (notificaciones Mongo)
