# Issue #572: Catálogos `GET /skills` y `GET /tools` — selector de skills y lista unificada de tools en los formularios

## Description

El esquema normalizado de #558 crea los catálogos **`skills`** y **`tools`**, pero nadie los
expone ni los consume. Hoy el frontend tiene:

- **Skills**: `CreateUserModal`/`EditUserModal` aceptan `skills: string[]` como texto libre
  (chips sin fuente única) mientras el backend hace upsert ciego (#559/#560).
- **Tools de agente**: **2 listas divergentes** — `AGENT_TOOLS` (9:
  `code_search, fs_read, fs_write, neo4j_query, web_search, github_pr, test_runner,
  docs_writer, shell` en `types/agentStudio.ts:21-47`) vs `EditAgentModal.vue:306-309` (8:
  `git-tools, neo4j-query, test-runner, file-manager, web-search, api-caller, code-analyzer,
  doc-writer`) — ni siquiera coinciden los slugs (`code_search` vs `code-analyzer`…). La
  validación de #564 exige una fuente única.

Origen: decisión del usuario "catálogo tools como roles/skills" (pregunta del plan v7).

## Status: TODO

## Priority: MEDIUM

## Component
Fullstack (Backend catálogos + formularios)

## Type
feat / fullstack

## Implementation
1. **Backend — endpoints de lectura** (router nuevo `catalogs.py` o en `user.py`):
   - `GET /skills` → `[{id, name}]` ordenado (sembrado en #558 + lo que upserteen
     #559/#560/#566).
   - `GET /tools` → `[{id, name, description}]` ordenado (seed de #558 = unión de las 2 listas
     actuales, decidida al implementar: slugs canónicos en snake_case + aliases en la
     migración de seed).
   - `APIResponse` envoltorio; 503 sin `TASKER_DATABASE_URL` (patrón de #564).
2. **Backend — validación**: los POST/PUT de `/users` y `/agents/profiles` validan
   `skills`/`tools` contra los catálogos (upsert de skills en #559/#560 ya contemplado; tools
   → 422 slug desconocido en #564 — reutilizar la misma función de validación).
3. **Frontend — API**: `catalogsApi.ts` (o en `usersApi`): `fetchSkills()`, `fetchTools()`
   con cache corta en el store (los catálogos cambian poco; cargar bajo demanda al abrir el
   modal).
4. **Frontend — picker de skills**: `CreateUserModal`/`EditUserModal` pasan el input de
   skills a **chips + datalist/autocomplete** con `GET /skills` (permiten valor libre que el
   backend upsertea).
5. **Frontend — lista unificada de tools**: `EditAgentModal` y el Studio (`AgentStudioView`
   checkboxes) consumen `GET /tools` en vez de sus constantes locales; `AGENT_TOOLS` queda
   como fallback en modo mock (`isMockMode()`). Slugs canónicos únicos.
6. **Tests** (obligatorios):
   - Backend: `test_get_skills_returns_catalog`, `test_get_tools_returns_catalog`,
     `test_create_user_unknown_skill_is_upserted` (si aplica), `test_create_agent_unknown_tool_422`
     (contrato compartido con #564), `test_catalogs_503_without_database_url`.
   - Frontend: `catalogsApi.spec.ts` (unwrap + tipos); spec de `EditAgentModal` o del picker —
     lista pintada desde el endpoint y selección enviada en el payload; en mock se usan las
     constantes locales.

## Acceptance Criteria
- [ ] `GET /skills` y `GET /tools` devuelven los catálogos desde PG (503 sin database)
- [ ] `EditAgentModal` y el builder del Studio renderizan sus tools desde `GET /tools` en real
      (fallback a constantes en mock) — **una sola lista**, fin de la divergencia
- [ ] Los formularios de usuario ofrecen autocomplete de skills desde `GET /skills`
      manteniendo valor libre (upsert en backend)
- [ ] Tools desconocidas → 422 en `/agents/profiles` (contrato #564)
- [ ] **Tests**: los pytest + specs listados pasan
- [ ] Gates: backend `ruff` 1011 / `mypy` 1153 / `pytest` 1331+3; frontend `lint` 0/2 /
      `test` 306+ (44+ files) / `build` OK / i18n 1693+ (claves EN/ES solo si se añaden)

## Files to Create
- `frontend/src/api/catalogsApi.ts` + `catalogsApi.spec.ts`
- (posible) `src/socialseed_tasker/infrastructure/web_api/routers/catalogs.py`
- `tests/api/test_catalogs_api.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` (registro)
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` / `agent_profiles.py`
  (validación compartida)
- `frontend/src/components/users/CreateUserModal.vue` / `EditUserModal.vue` (picker skills)
- `frontend/src/components/users/EditAgentModal.vue` (tools desde endpoint)
- `frontend/src/views/AgentStudioView.vue` + `frontend/src/types/agentStudio.ts` (fallback)
- `tests/api/test_users_api.py` / `test_agent_profiles_api.py`

## Notes
- Los slugs canónicos de tools se fijan en el seed de #558 (unión de las 2 listas, snake_case)
  — este issue no cambia `agents_user.tools`, solo la fuente del frontend y la validación.
- Catálogo de roles (`GET /roles`) **no** hace falta: el select de rol usa las claves
  i18n existentes (#556).

## Related Issues
- #558 (catálogos + seeds), #559/#560 (upsert de skills), #564 (validación de tools), #566
  (crear agente con skills/tools), #573 (Studio consume el catálogo)
