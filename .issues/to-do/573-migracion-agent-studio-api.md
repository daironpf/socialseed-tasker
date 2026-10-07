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

## Status: TODO

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
- [ ] En modo real, crear/editar/clonar/activar/eliminar en Studio persiste en
      `/agents/profiles` (PG) y sobrevive a recargar el navegador
- [ ] Importación única de los perfiles `agent-studio-*` existentes (idempotente, con aviso)
- [ ] Modo mock intacto: localStorage sigue funcionando sin llamadas de red
- [ ] La tarjeta del agente importado aparece en la vista de Usuarios con uid PG
- [ ] Sandbox del Studio sin cambios funcionales
- [ ] **Tests**: spec de `agentStudioStore` + importación pasan
- [ ] Gates frontend: `lint` 0 errors / 2 warnings, `test` 306+ (44+ files), `build` OK,
      i18n 1693+N EN/ES (aviso de importación)
- [ ] `pendingFeatures` deja de marcar `/agents/studio` en real (si aplica tras la migración)

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
