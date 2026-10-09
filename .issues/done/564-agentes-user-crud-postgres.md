# Issue #564: CRUD de perfiles de agente en PostgreSQL — endpoint dedicado `/agents/profiles`

## Description

Decisión del usuario: los agentes de la vista de Usuarios **no van en el endpoint genérico
`/users`** (que es de humanos y está sujeto al guard de último rol) sino en un **endpoint
dedicado `/agents/profiles`** sobre la raíz PG con la tabla **`agents_user`** (ya creada y
sembrada en el esquema normalizado de **#558**). Agent Studio se migra en **#573** (no aquí).

Realidad actual:

- Los agentes de la vista viven **solo en localStorage** (`agent-studio-v1`,
  `utils/studioAgents.ts` → `mergeStudioAgents`, ids `agent-studio-*`) — no hay API.
- `/users` no soporta agentes: editar/borrar una tarjeta IA contra la API → 404.
- `agent.py` registra rutas `/agents/{agent_id}` — una ruta `/agents/profiles`
  **colisionaría** con el path param `agent_id` si se registra después → registrar el router
  de perfiles **antes** en `app.py` (o prefijo `/agent-profiles`; por defecto:
  **mismo prefijo `/agents/profiles` con `app.include_router` antes** del router de
  `agent.py`).

Esquema (de #558, aquí solo se consume): `agents_user(user_id PK→users ON DELETE CASCADE,
email, avatar, model, specialization, temperature, system_prompt, tools JSONB, write_access
JSONB, limits JSONB, enabled, last_used_at)` — la identidad es la fila `users`
(`user_type='agent'`, uid generado por PG, sin `password_hash`, **sin `role_id`**: los roles
son de RBAC humano). `tools` se valida contra el catálogo `tools` (#558/#572).

Mock de referencia (`users.json`, entradas `type:'agent'`): `id, username, email,
role:'ai-agent', type:'agent', avatar, created_at, last_active, issues_assigned,
issues_created, skills[], model, specialization` + `EditAgentModal` emite además
`temperature, systemPrompt, tools, writeAccess, limits`.

## Status: DONE

## Priority: HIGH

## Component
Backend / Data / PostgreSQL

## Type
feat / backend

## Implementation
1. **Repositorio** (patrón `user_store`, `psycopg` + `closing`): CRUD transaccional sobre
   `users` + `agents_user` + `user_skills`:
   - `list_agent_profiles`: JOIN `users ⨝ agents_user ⨝ user_skills/skills`.
   - `create`: `INSERT users (user_type='agent', RETURNING uid)` + `INSERT agents_user` +
     skills upsert; `tools` validadas contra el catálogo → **422** slug desconocido.
   - `update`: `UPDATE agents_user` (+ `user_skills` si cambian skills; username en `users`)
     → 404 sin fila, 409 username duplicado.
   - `delete`: `DELETE FROM users WHERE id` (la cascada FK limpia `agents_user` y
     `user_skills`) — transacción.
   - Tests con fake o PG real.
2. **Nuevo router** `routers/agent_profiles.py` con `APIResponse`:
   - `GET /agents/profiles` → lista completa (uid PG, username, email, avatar, model, skills,
     specialization, tools, write_access, temperature, system_prompt, enabled, created_at,
     last_used_at; `role` → `null`, el front deriva `'ai-agent'`).
   - `GET /agents/profiles/{agent_id}` → 404 si no existe.
   - `POST /agents/profiles` → payload `AgentProfileCreate` (username, email?, avatar, model,
     skills, specialization, temperature?, systemPrompt?, tools?, writeAccess?, limits?,
     enabled?) → 201 con fila completa + uid PG.
   - `PUT /agents/profiles/{agent_id}` → actualiza; 404 sin fila; 409 username duplicado;
     422 tool desconocida.
   - `DELETE /agents/profiles/{agent_id}` → 200; **sin guard de último humano**; 404 si no.
   - Sin `TASKER_DATABASE_URL` → 503.
3. **Registro de rutas en `app.py`**: incluir el router de `agent_profiles` **antes** de
   `agent.py` (test de orden: `GET /agents/profiles` no cae en `/{agent_id}`).
4. **Tests** (obligatorios): `tests/api/test_agent_profiles_api.py`:
   `test_list_agent_profiles_empty`, `test_create_agent_profile_201_returns_uid`,
   `test_create_agent_profile_unknown_tool_422`, `test_get_agent_profile_404`,
   `test_update_agent_profile`, `test_delete_agent_profile_removes_users_and_agents_user_rows`,
   `test_agent_profile_route_registered_before_agent_id`,
   `test_agent_profile_no_login_with_missing_credential`, `test_agent_profiles_503_without_database_url`.

## Acceptance Criteria
- [x] `GET/POST/PUT/DELETE /agents/profiles` funcionan sobre `users` + `agents_user` con uid
      generado por la raíz
- [x] `tools` desconocida → 422; username duplicado → 409; sin database → 503
- [x] El registro de rutas no colisiona con `/agents/{agent_id}` (test explícito)
- [x] Los agentes no pueden iniciar sesión (sin fila `human_user`/credencial)
- [x] `DELETE /users/{id}` de un agente limpia `agents_user`/`user_skills` por `CASCADE` (y
      el guard de humanos no aplica a los agentes)
- [x] **Tests**: los pytest listados pasan
- [x] Gates backend sin regresiones: `ruff` 1334, `mypy` 1136, `pytest` 1437 (+11, 3
      preexistentes documentados)

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/routers/agent_profiles.py`
- `tests/api/test_agent_profiles_api.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` (orden de routers)
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`AgentProfileCreate/Update/
  Response`)
- `src/socialseed_tasker/auth/user_store.py` o repo nuevo (CRUD de agentes)

## Notes
- El DDL de `agents_user` **no** vive aquí (es de #558); este issue es repo + API.
- El formato se alinea con `EditAgentModal` (front) y las entradas `type:'agent'` de
  `users.json` — `enabled` ↔ `is_active` de la tarjeta; `role` se deriva en el front.
- **La migración de Agent Studio a esta API es #573** (aquí solo el endpoint); el dispatch
  de #567/#568 por prefijo `agent-studio-*` se mantiene hasta entonces.
- Colisión FastAPI verificada: `include_router(agent_router)` con `/agents/{agent_id}`
  capturaría `/agents/profiles` si va primero.

## Related Issues
- #558 (esquema + `agents_user` + catálogo `tools`), #559/#560 (humanos en `/users`), #562
  (borrado en cascada), #565 (listado en la vista), #566-#568 (alta/edición/borrado desde la
  vista), #572 (catálogos skills/tools API+UI), #573 (migración del Studio)

## Resolution

Implementado 2026-10-08 (commit pendiente de `si`):

- **Store** `PostgresAgentProfileStore` (`auth/user_store.py`): CRUD transaccional sobre
  `users` + `agents_user` + `user_skills`; uid generado por PG (`RETURNING id`,
  `user_type='agent'`); `tools` validadas contra el catálogo (`ValueError('tool:<slug>')`);
  JSONB pasados como texto con cast explícito `::jsonb`; update parcial con `None` = keep
  (lectura previa de los valores actuales); skills con reemplazo total; `delete_profile` con
  guard `WHERE user_type='agent'` (nunca toca humanos, que van por `DELETE /users` #562).
- **Router** `routers/agent_profiles.py`: `GET/GET{id}/POST/PUT/DELETE /agents/profiles`
  con `APIResponse`; 404 sin fila (get/update/delete), 409 username duplicado, 422 tool
  desconocida o username vacío, 503 sin `TASKER_DATABASE_URL`. `role` siempre `null` (el
  front deriva `ai-agent`), `type='agent'`.
- **app.py**: `include_router(agent_profiles_router)` **antes** de `agent_router` (test
  `test_agent_profile_route_registered_before_agent_id` fija el orden).
- **Fake** `FakePgCursor`: `self.tools` catalog; insert/update `agents_user` completos (11
  params) sin romper la forma legada de 2/4; `delete from users` con detección del literal
  `'agent'`; handlers de `select 1 from users where id`, `select 1 from tools where id`,
  snapshot JSONB del update, fila de perfil `users ⨝ agents_user` y join de skills.
- **Tests** `tests/api/test_agent_profiles_api.py` (11): los 9 obligatorios del issue +
  `test_delete_agent_profile_never_touches_humans` y
  `test_create_agent_profile_duplicate_username_409`.
- Frontend intacto (migración del Studio = #573). Gates: ruff 1334 / mypy 1136 /
  pytest 1437 (+11; los 3 fallos son los preexistentes documentados).
