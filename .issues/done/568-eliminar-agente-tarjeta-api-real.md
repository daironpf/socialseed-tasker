# Issue #568: Eliminar agente desde la tarjeta contra la API real (`DELETE /agents/profiles/{id}`)

## Description

El borrador de tarjeta IA en `UsersView.deleteAgent`/`removeAgent` llama hoy `DELETE /users/{id}`:

- En real, los agentes del endpoint **no están en `/users`** → **404** (o se intentaría borrar
  con el guard de "último humano", que no debe aplicarse a agentes).
- Los agentes locales `agent-studio-*` no existen en backend → 404; deben borrarse de
  localStorage (mecanismo de Agent Studio).

Con #564 el borrado real es `DELETE /agents/profiles/{id}` — **sin guard de humanos** (el guard
solo cuenta humanos en PG, #562) — y como el agente es una fila `users` + su perfil
`agents_user`, el DELETE de la raíz limpia `agents_user`/`user_skills` por **FK `ON
DELETE CASCADE`** (esquema #558/#564).

Mock de referencia: `mockApi.deleteUser` elimina la entidad y desaparece de la lista.

## Status: DONE

## Priority: MEDIUM

## Component
Fullstack (store + agentProfilesApi + UsersView)

## Type
feat / fullstack

## Implementation
1. **`usersStore.deleteAgent(user)`** (nuevo) con la misma ramificación de #567:
   - `id.startsWith('agent-studio-')` → eliminar de localStorage/Agent Studio, sin red.
   - resto → `deleteAgentProfile(id)` (#565) → éxito ⇒ quitar la tarjeta del store.
2. **Backend — garantizar que borrar el perfil borra la raíz**: el agente es fila `users` +
   fila `agents_user`; `DELETE /agents/profiles/{id}` ejecuta `DELETE FROM users WHERE id`
   **en transacción** y la cascada FK limpia `agents_user` y `user_skills` (si #564 ya lo
   trae, aquí solo se comprueba en AC).
3. **Frontend — errores**: 404 (ya borrado) → toast con `detail` + refetch; 503 →
   `common.error`; el store no muta la lista en error.
4. **Sin guard de "último"**: confirmación del borrado en la vista (ya existe el patrón de
   `confirmDelete`/modal de confirmación de #556) — los agentes siempre se pueden borrar.
5. **Tests** (obligatorios):
   - Frontend: spec de `deleteAgent` — id PG → `DELETE /agents/profiles/{id}` y tarjeta
     retirada; id `agent-studio-*` → sin red, retirada de localStorage; humanos → sigue
     yendo a `deleteUser` con el 409 del guard (no-regresión #556); 404 → error y tarjeta
     intacta.
   - Backend (contrato #564): `test_delete_agent_profile_removes_users_and_agents_user_rows`
     — tras DELETE, ni `users` ni `agents_user` tienen la fila (cascada) y el agente no puede
     "loguearse" (ya era imposible por falta de credencial).

## Acceptance Criteria
- [x] Borrar una tarjeta IA en real llama a `DELETE /agents/profiles/{id}` y la fila `users`
      asociada desaparece de la raíz (`agents_user` limpia por cascada)
- [x] El guard de último humano **nunca** bloquea el borrado de agentes (pero sigue bloqueando
      el de humanos, #562)
- [x] Los agentes locales se borran de localStorage sin llamadas de red
- [x] 404/503 → toast con detalle y la tarjeta no se retira
- [x] **Tests**: spec frontend `deleteAgent` + test backend de cascada `users`/`agents_user`
      pasan
- [x] Gates: backend `ruff` 1011 / `mypy` 1153 / `pytest` 1331+3; frontend `lint` 0/2 /
      `test` 306+ / `build` OK

## Files to Create
- (posible) extensión de `usersStore.spec.ts`

## Files to Modify
- `frontend/src/stores/usersStore.ts` (`deleteAgent`/dispatch)
- `frontend/src/views/UsersView.vue` (handler de borrado por tipo)
- `frontend/src/api/agentProfilesApi.ts` (delete)
- `src/socialseed_tasker/infrastructure/web_api/routers/agent_profiles.py` (DELETE de la raíz
  con cascada a `agents_user` si no lo trae #564)
- `tests/api/test_agent_profiles_api.py`

## Notes
- Orden del lote: #564 (endpoint con cascada) → #565 (api front) → #568 (borrado vista);
  #566/#567 pueden ir en paralelo con #568.
- No confundir con el borrado de **humanos** (#562): ese sí tiene guard 409 y cascada Neo4j/
  Mongo.

## Related Issues
- #556 (guard 409 y borrado de humanos), #562 (borrado raíz en cascada), #564/#565 (endpoint y
  api de perfiles), #567 (edición paralela)

## Resolution

Implementado 2026-10-09 (commit pendiente de `si`):

- **Solo frontend** — el backend ya lo traía #564: `test_delete_agent_profile_removes_users_and_agents_user_rows`
  y `test_delete_agent_profile_never_touches_humans` existen desde esa issue (suite
  `tests/api/test_agent_profiles_api.py` 11/11 OK) y el `DELETE` es transaccional con
  cascada FK a `agents_user`/`user_skills` verificada en vivo en el smoke de #564.
- **`usersStore.deleteAgent(user)`** con la ramificación de #567: id `agent-studio-*` →
  `removeStudioProfile()` (nuevo en `utils/studioAgents.ts`: filter+save sobre
  `agent-studio-v1`, sin red) · mock mode → `api.deleteUser` (la colección mock es dueña de
  sus entidades, #566) · real → `deleteAgentProfile(id)` → `DELETE /agents/profiles/{id}` →
  éxito ⇒ tarjeta fuera del store. Humanos **nunca** entran aquí: la plantilla ya despacha
  por `v-if="user.type"` (humano → `deleteUser` con guard 409 de #562 y botón
  `disabled=isLastHuman`; agente → `deleteAgent`, botón siempre habilitado).
- **Errores**: el store relanza sin mutar la lista; en **404** dispara `fetchUsers()` antes
  de registrar el error (mismo orden que #567 — `fetchUsers` limpia `error` al arrancar) y
  la vista pinta `common.error: detail` (404/503 con detalle, fallback `common.error`),
  cerrando `EditAgentModal` solo en éxito.
- **Sin modal de confirmación**: no figura en los AC y el borrado de humanos tampoco lo
  tiene (consistencia de la vista); el AC "los agentes siempre se pueden borrar" se cumple
  porque el botón de tarjeta agente no aplica el guard `isLastHuman`.
- **Tests** (+5 en `usersStore.spec`, describe `usersStore.deleteAgent (issue #568)`):
  id PG → `deleteAgentProfile` y tarjeta retirada; `agent-studio-*` → localStorage vaciado
  sin tocar APIs (incluso en mock); rama mock → `api.deleteUser`; 404 → rechaza, tarjeta
  intacta y refetch; humano → `deleteUser` relanza el 409 con la tarjeta intacta
  (no-regresión #562/#556). `UsersView.spec` añade `deleteAgentProfile` a la factory.
- Gates: backend sin cambios (ruff 1334 / mypy 1136 / pytest 1437 baselines intactos) +
  suite `test_agent_profiles_api.py` 11/11; frontend `lint` 0/2, `test` 350 (47 files, +5),
  `build` OK, i18n sin cambios (1702/1702).
