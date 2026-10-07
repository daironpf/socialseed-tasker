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

## Status: TODO

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

## Acceptance Criteria
- [ ] Tras `DELETE /users/{id}`, la fila PG no existe y **ese usuario no puede iniciar sesión**
- [ ] El guard de último humano cuenta en **PG** y responde 409 sin borrar nada
- [ ] Las sesiones/refresh del usuario borrado quedan revocadas (refresh → 401)
- [ ] Proyección Neo4j y `notifications` de Mongo del id PG se limpian best-effort (degradan a
      log sin servicios)
- [ ] 404 al borrar un id inexistente
- [ ] **Tests**: los pytest listados + frontend pasan
- [ ] Gates backend sin regresiones: `ruff` 1011, `mypy` 1153, `pytest` 1331+3; frontend
      `lint` 0/2 / `test` 306+ / `build` OK si toca UI

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
