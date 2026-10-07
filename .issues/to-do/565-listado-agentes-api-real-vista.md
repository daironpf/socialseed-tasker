# Issue #565: Listado de agentes en la vista desde la API real (merge PG + profiles API + localStorage)

## Description

`UsersView` construye la lista con `usersStore.fetchUsers()` → `GET /users` (humanos) y luego
`mergeStudioAgents()` añade los agentes de **localStorage** (`agent-studio-v1`). Con la API de
**#564**, los agentes reales viven en `/agents/profiles` y el listado debe ser la unión de:

1. Humanos desde `GET /users` (PG, #558).
2. Agentes desde `GET /agents/profiles` (PG, #564).
3. Los agentes locales `agent-studio-*` de localStorage (Agent Studio, decisión: seguir
   soportándolos en la vista hasta su migración opcional — ids con prefijo para no colisionar
   con los id PG).

`fetchUsers` hoy solo llama a `/users` → los agentes del endpoint quedan invisibles. Además
`UserResponse` de `/users` ya no traerá `type:'agent'` (los agentes no están en ese endpoint),
pero la normalización debe seguir tolerando payload mixto (mock sí mezcla agentes en `/users`).

Mock de referencia: `mockApi.listUsers` devuelve humanos **y** agentes en una sola colección
(la vista no distingue origen) — en real el store simula esa colección unificada.

## Status: TODO

## Priority: HIGH

## Component
Fullstack (frontend store/api + usersApi)

## Type
feat / fullstack

## Implementation
1. **`frontend/src/api/agentProfilesApi.ts`** (nuevo): `fetchAgentProfiles()`,
   `createAgentProfile()`, `updateAgentProfile()`, `deleteAgentProfile()` contra
   `/agents/profiles` con `client.get/post/put/delete` y unwrap de `APIResponse` (mismo patrón
   que `usersApi`); tipos locales `AgentProfile` alineados con `EditAgentModal`.
2. **`usersStore.fetchUsers`**: recuperar **en paralelo** humanos (`fetchUsers` de usersApi)
   + perfiles (`fetchAgentProfiles`) + mantener `mergeStudioAgents` sobre los locales; merge
   final deduplicando por id (localStorage no pisa ids PG); en modo mock solo la llamada
   mock/`/users` (los perfiles no existen en mock → `get` falla silencioso o se salta con
   `isMockMode()`, decidir: **en mock, solo mock**).
3. **Errores no rompen la vista**: si `/agents/profiles` devuelve 503 (sin database) la lista
   de humanos se muestra igual (log/estado parcial, patrón de tolerancia ya usado en la vista).
4. **Estadísticas IA**: `stats` de la vista (usuarios/agentes/issue asignados…) deben contar
   los perfiles del endpoint además de los locales (hoy cuenta solo los del store).
5. **Respuestas normalizadas**: cada perfil se convierte al shape `User` de la tarjeta
   (`type:'agent'`, avatar, skills, model, specialization, `is_active`→`enabled`, id PG).
   Los perfiles de PG traen `role: null` (los agentes no tienen `role_id`, esquema #558) →
   `normalizeBackendUser` deriva `'ai-agent'` para `type==='agent'` (mock lo trae explícito).
6. **Tests** (obligatorios):
   - `agentProfilesApi.spec.ts` — unwrap del envelope, payload de perfil, manejo de 503/404.
   - Ampliar el spec de `usersStore` (o `usersApi.spec`): `fetchUsers` combina `/users` +
     `/agents/profiles` + locales sin duplicados; fallo de profiles no vacía la lista;
     modo mock no llama a `/agents/profiles`.

## Acceptance Criteria
- [ ] La lista de la vista muestra humanos (PG), agentes de `/agents/profiles` (PG) y locales
      `agent-studio-*` sin duplicados por id
- [ ] Modo mock intacto: solo datos del mock, sin llamadas nuevas
- [ ] 503/error de `/agents/profiles` no impide ver los humanos
- [ ] El contador "agentes" incluye los perfiles del endpoint
- [ ] **Tests**: `agentProfilesApi.spec.ts` + spec de combinación del store pasan
- [ ] Gates frontend: `lint` 0 errors / 2 warnings, `test` 306+ (44+ files), `build` OK,
      i18n sin cambios o 1693+ si se añade clave

## Files to Create
- `frontend/src/api/agentProfilesApi.ts`
- `frontend/src/api/agentProfilesApi.spec.ts`

## Files to Modify
- `frontend/src/stores/usersStore.ts` (+ su spec si existe)
- `frontend/src/utils/studioAgents.ts` (ajuste del merge para no pisar ids PG)
- (posible) `frontend/src/views/UsersView.vue` (stats)

## Notes
- La **creación/edición/borrado** de tarjetas IA es #566/#567/#568 — aquí solo lectura.
- Los ids `agent-studio-*` distinguen los locales de los id PG en la fusión; si Agent Studio
  migra después (#extra), el merge queda como capa de compatibilidad.

## Related Issues
- #558 (humanos PG), #564 (endpoint de perfiles), #566-#568 (escrituras), #547/#549 (patrón de
  api client/`APIResponse`), Agent Studio migración (opcional, fuera de este lote)
