# Issue #573: Migración de Agent Studio a la API — builder sobre `/agents/profiles`

## Description

Agent Studio (`AgentStudioView` + `agentStudioStore` + localStorage `agent-studio-v1`) es
hoy **100 % frontend**: el builder de perfiles (nombre, modelo, system prompt con variables,
tools, límites, sandbox mock, biblioteca con clonar/activar/eliminar) guarda en el navegador y
**no sobrevive a otro dispositivo ni a un reinicio limpio**. Los agentes creados aquí solo
aparecen en la vista de Usuarios por el merge de `mergeStudioAgents`.

Decisión del usuario (reemplaza la decisión previa "Studio solo localStorage"): **el Studio
pasa a usar la API real** — el perfil YA existe como `users(user_type='agent')` +
`agents_user` (esquema #558, CRUD #564), así que **no hay tabla nueva**: se migra el
consumidor. `pendingFeatures.ts:37` marca `/agents/studio` como feature pendiente en modo
real → esta issue lo habilita.

## Status: DONE

## Resolution

Implementado 2026-10-10.

**Backend** (soporte para `markUsed`):
- `AgentProfileUpdate` gana `last_used_at: datetime | None` (`schemas.py`); `update_profile`
  (`auth/user_store.py`) lo lee en el pre-SELECT y lo escribe en el UPDATE (None = keep);
  el router lo reenvía. Test nuevo `test_update_agent_profile_last_used_at` (persiste y
  sobrevive a updates parciales posteriores). `FakePgCursor` actualizado (SELECT 11-tuple,
  UPDATE 12 valores).

**Frontend**:
- `agentProfilesApi.ts`: `fetchAgentProfilesRaw()`/`createAgentProfileRaw()` (las variantes
  card normalizan y pierden `limits`/`last_used_at`, que el Studio necesita) +
  `AgentProfilePayload.last_used_at`.
- `studioAgents.ts`: `backendProfileToStudio`/`studioProfileToPayload` (el `role` libre del
  Studio viaja en `specialization`, agents no tienen RBAC), `wasStudioImported`/
  `markStudioImported` (flag `agent-studio-v1-imported`).
- `agentStudioStore.ts`: `loadProfiles()` (real → `GET /agents/profiles` + importación
  única previa; mock → localStorage); `saveProfile`/`cloneProfile`/`toggleEnabled`/
  `removeProfile`/`markUsed` async con rama `isMockMode()` (mock = localStorage sin red;
  real = POST/PUT/DELETE, toast de error y `refreshUsers()`); importación idempotente:
  un POST por perfil local `agent-studio-*`, flag marcado, clave legada vaciada, aviso
  `agentStudio.imported` EN/ES; si la API falla, degrada a la copia local.
- `AgentStudioView.vue`: `save()` async, `onMounted` llama `store.loadProfiles()`,
  `onSandboxUsed` → `void store.markUsed` (sandbox intacto por diseño).
- `pendingFeatures.ts`: `/agents/studio` fuera de la lista (badge y chip "Under
  construction" retirados en ambos modos).
- i18n: `agentStudio.imported` EN/ES.
- Notas añadidas en #567/#568 (done): la rama `agent-studio-*` queda como fallback solo
  para perfiles legados no importados.

**Tests**: `agentStudioStore.spec.ts` (14: mapeo, create/update/toggle/remove/clone/markUsed
sobre API en real, errores sin mutar, mock local sin red, importación única + flag + fallo
parcial no bloquea).

**Gates**: ruff 1251 (neutral) / mypy idéntico al baseline / pytest 1460+3 preexistentes+27
skipped; lint 0/2 / test 381 (50 files) / build OK / i18n 1704/1704.

**Nota live**: la importación se dispara al abrir el Studio (`AgentStudioView.onMounted`);
hasta entonces los perfiles legados siguen sirviendo la rama local de #567/#568.

## Priority: HIGH

## Component
Fullstack (Agent Studio + agentProfilesApi)

## Type
feat / fullstack

## Implementation
1. **Frontend — `agentStudioStore` sobre la API**:
   - `loadProfiles()` → en real `fetchAgentProfiles()` (#565); en mock sigue
     `loadStudioProfiles()` (localStorage) — rama por `isMockMode()`.
   - `saveProfile/create` → `POST /agents/profiles`; `update` → `PUT`;
     `remove` → `DELETE`; `toggleEnabled` → `PUT` con `enabled`; `cloneProfile` → `POST` con
     nombre "… (copia)". Respuestas normalizadas al shape `AgentProfile` del Studio
     (mapear `system_prompt ↔ systemPrompt`, `limits`, `tools`, `enabled`).
   - `markUsed(id)` → `PUT` con `last_used_at = now()` (columna ya existe en `agents_user`).
2. **Importación única de perfiles locales**: al detectar ids `agent-studio-*` en localStorage
   con la API disponible → `POST /agents/profiles` por cada uno (crea uid PG), y **reasignar**
   el id local en la vista/store; dejar de leer esa clave (o vaciarla con aviso
   `studio.imported` EN/ES: "Perfiles importados a la base de datos"). Idempotente: no
   re-importar los ya migrados (marcar con flag en localStorage `agent-studio-v1-imported`).
3. **Sandbox**: el tester determinista local se queda como está (es mock por diseño) — fuera
   de alcance; solo persistencia del perfil.
4. **Contratos heredados**: el dispatch por prefijo `agent-studio-*` de #567/#568 solo queda
   para perfiles legados no importados; documentar en esas issues que esta migración lo retira
   (actualizar sus Notes).
5. **Vista Usuarios**: `fetchUsers` (#565) puede dejar de fusionar locales en real tras la
   importación (mantener en mock); `mergeStudioAgents` queda como fallback local.
6. **Tests** (obligatorios):
   - Frontend: spec de `agentStudioStore` (no existe hoy) — guardar → `POST`, editar → `PUT`,
     toggle/eliminar → API en real; en mock → localStorage sin llamadas; importación → una
     llamada por perfil local y flag marcado (no re-importa).
   - Ampliar `studioAgents.spec.ts` si cambia el contrato de merge.

## Acceptance Criteria
- [x] En modo real, crear/editar/clonar/activar/eliminar en Studio persiste en
      `/agents/profiles` (PG) y sobrevive a recargar el navegador
- [x] Importación única de los perfiles `agent-studio-*` existentes (idempotente, con aviso)
- [x] Modo mock intacto: localStorage sigue funcionando sin llamadas de red
- [x] La tarjeta del agente importado aparece en la vista de Usuarios con uid PG
      (`refreshUsers()` + refetch de UsersView al montar)
- [x] Sandbox del Studio sin cambios funcionales (`markUsed` best-effort tras `@used`)
- [x] **Tests**: spec de `agentStudioStore` + importación pasan (14/14)
- [x] Gates frontend: `lint` 0/2, `test` 381 (50 files), `build` OK, i18n 1704/1704
      (`agentStudio.imported` EN/ES); backend pytest 1460+3 preexistentes
- [x] `pendingFeatures` deja de marcar `/agents/studio`

## Files to Create
- `frontend/src/stores/agentStudioStore.spec.ts`

## Files to Modify
- `frontend/src/stores/agentStudioStore.ts` (carga/guardado sobre API + importación)
- `frontend/src/utils/studioAgents.ts` (merge como fallback; flag de importación)
- `frontend/src/api/agentProfilesApi.ts` (si #565 no lo cubre del todo)
- `frontend/src/utils/pendingFeatures.ts` (quitar `/agents/studio` si aplica)
- `frontend/src/views/AgentStudioView.vue` (toasts de éxito/error API)
- `frontend/src/locales/es.json` / `en.json`
- `.issues/to-do/567-*.md` / `568-*.md` (notas de retiro del branch local)

## Notes
- **No revivir la tabla `agent_studio`**: el perfil YA es `users` + `agents_user` (#558) —
  SRP, cero duplicación.
- Los drafts a medio hacer pueden seguir en localStorage (form no guardado) — solo los
  perfiles guardados se migran.
- Skills del Studio → `skills`/`user_skills` (upsert) y tools → catálogo (#572).
- Orden: tras **#564** (endpoint) y **#565** (api client); puede ir en paralelo con
  #566-#568.

## Related Issues
- #558/#564 (esquema y CRUD de agentes), #565 (agentProfilesApi), #567/#568 (dispatch que
  retira), #572 (catálogo tools), #574 (historial de ejecuciones del Studio, siguiente paso),
  #513 (issue original del Studio, DONE)
