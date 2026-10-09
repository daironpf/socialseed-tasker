# Issue #567: Editar agente desde la tarjeta contra la API real (`PUT /agents/profiles/{id}`)

## Description

Al editar una tarjeta IA, `UsersView.saveAgent` / `EditUserModal`-`EditAgentModal` llaman hoy
`PUT /users/{id}` con el id de la tarjeta. En real:

- Los agentes **del endpoint** (id PG, #564) no están en `/users` → **404**.
- Los agentes **locales** `agent-studio-*` no existen en ningún backend → 404 también (hoy
  funcionan porque en mock `/users` los conoce, o se quedan tocados solo en memoria).

El flujo debe ramificar: **id `agent-studio-*` → localStorage (Agent Studio)**;
**cualquier otro id → `PUT /agents/profiles/{id}`**. La respuesta convertida al shape `User`
actualiza la tarjeta (igual criterio de normalización que #566).

Mock de referencia: `mockApi.updateUser` devuelve la entidad completa actualizada y la tarjeta
se re-renderiza intacta (badge IA, avatar, model…).

## Status: DONE

## Priority: MEDIUM

## Component
Fullstack (modal + store + agentProfilesApi)

## Type
feat / fullstack

## Implementation
1. **`usersStore.updateAgent(user)`** (nuevo) con la ramificación:
   - `id.startsWith('agent-studio-')` → persistir en localStorage vía `agentStudioStore`/
     `saveStudioProfiles` (mismo mecanismo actual de Agent Studio) y devolver el usuario
     actualizado localmente.
   - resto → `updateAgentProfile(id, payload)` (#565) → respuesta convertida a `User`.
2. **`UsersView.saveAgent`/handler de edición**: si `user.type === 'agent'` (o `id` no es de
   humano) → `updateAgent`; humanos siguen en `updateUser` (#560). Evitar doble dispatch:
   centralizar la decisión en el store (`editUser(user)` que ramifica por `type`/prefijo) y
   testearla.
3. **Payload de `EditAgentModal`**: mapear los campos del form al contrato
   `AgentProfileUpdate` (model, specialization, skills, avatar, temperature, systemPrompt,
   tools, writeAccess, limits, enabled) — el modal actual ya emite esos nombres
   (`systemPrompt`, `writeAccess`, …) y el backend los recibe en camelCase/snake según
   fijado en #564 (mantener consistencia: **camelCase en request de perfiles**, como en el
   resto de la API).
4. **Errores**: 404 (perfil borrado en backend) → toast con `detail` y refetch de la lista;
   409 username duplicado → `users.usernameTaken`; 422/503 → `common.error`.
5. **Tests** (obligatorios): spec de `updateAgent`/`editUser` del store:
   - id PG → `PUT /agents/profiles/{id}` con payload completo y tarjeta actualizada con la
     respuesta normalizada (regresión de respuesta cruda).
   - id `agent-studio-*` → **no** llama a la API, persiste en localStorage y la tarjeta se
     actualiza localmente.
   - humanos → sigue llamando a `updateUser` (`/users/{id}`) — test de no-regresión.
   - 404 → error propagado (el store no actualiza la tarjeta).

## Acceptance Criteria
- [x] Editar un agente del endpoint en real hace `PUT /agents/profiles/{id}` y la tarjeta
      conserva tipo/avatar/model/skills tras guardar
- [x] Editar un agente local `agent-studio-*` funciona sin red (localStorage) y sigue
      funcionando en mock
- [x] Los humanos no cambian de endpoint (test de no-regresión)
- [x] 404/409/422/503 → toast con detalle y sin mutar la tarjeta
- [x] **Tests**: los specs de store listados pasan (+5: payload exacto, studio en localStorage
      en mock, humano no-regresión, rama mock, 404 sin mutar + refetch)
- [x] Gates frontend: `lint` 0/2, `test` **345 (47 files, +5)**, `build` OK, i18n 1702/1702
      (sin claves nuevas)

## Files to Create
- (posible) extensión de `usersStore.spec.ts`

## Files to Modify
- `frontend/src/stores/usersStore.ts` (`updateAgent`/`editUser` con dispatch)
- `frontend/src/views/UsersView.vue` (handler de guardado por tipo)
- `frontend/src/components/users/EditAgentModal.vue` (mapeo de payload si hace falta)
- `frontend/src/utils/studioAgents.ts` / store de Agent Studio (persistencia)
- specs frontend afectados

## Notes
- Decisión #547-style: centralizar el dispatch en el store en vez de en la vista para poder
  testear sin montar `UsersView` completo (aunque #560 añade un spec de vista, este ramificado
  se prueba a nivel store).
- Agent Studio local es la ruta de migración futura — mantener el prefijo como contrato.
  La **migración real del Studio a la API** es la issue **#573**: cuando cierre, la rama
  localStorage de este dispatch se retira (o queda solo para perfiles legados no importados).

## Related Issues
- #560 (edición de humanos), #564/#565 (endpoint y api de perfiles), #566 (creación),
  #568 (borrado paralelo), #556/#559 (normalización de respuesta)

## Resolution

Implementado 2026-10-09 (commit pendiente de `si`):

- **Dispatch centralizado en el store**: `usersStore.editUser(data)` ramifica en orden —
  1) id `agent-studio-*` → `applyStudioUpdate()` en `utils/studioAgents.ts` (localStorage
  `agent-studio-v1`, sin red, funciona también en mock; merge `skills+tools` → `profile.tools`
  porque la tarjeta mapea `tools→skills`); 2) mock mode → `api.updateUser` (la colección mock
  es dueña de sus entidades, igual que `createAgent` #566); 3) `type==='agent'` en real →
  `updateAgentProfile(id, toProfilePayload(data))` → `PUT /agents/profiles/{id}`; 4) humanos →
  `updateUser` (#560 intacto). El payload se filtra a los 10 campos del contrato (snake_case,
  ya es lo que emite el modal) — `id/role/type/issues_*/is_active/enabled` no viajan y
  `limits` se conserva en backend (update parcial None=keep, #564).
- **Round-trip de campos**: `User` gana `system_prompt?/temperature?/tools?/write_access?`
  opcionales; `normalizeAgentProfile` los asigna **solo si existen** en la respuesta (una key
  con `undefined` anularía los defaults del modal al hacer spread) y `profileToUser` (studio)
  expone `systemPrompt` como `system_prompt`. Así el modal de edición no machaca prompt/
  temperatura/herramientas reales con valores por defecto en cada guardado.
- **Errores**: el store propaga sin mutar la tarjeta; en **404** dispara `fetchUsers()` (la
  tarjeta obsoleta desaparece del listado — cuidado con el orden: `fetchUsers` limpia
  `error` en su arranque síncrono, así que el refetch se lanza *antes* de registrar el
  error). La vista mapea toasts: 409 → `users.usernameTaken`/`users.emailTaken`,
  422/404 → `common.error: detail`, resto → `common.error`.
- **Modal**: `EditAgentModal.save()` ya solo emite (antes cerraba siempre); `UsersView`
  cierra en éxito — en error el formulario queda abierto (consistente con #566).
- **Tests** (+5 en `usersStore.spec`): payload exacto de PUT con tarjeta reemplazada por la
  respuesta normalizada; studio en localStorage sin tocar APIs (en modo mock); humano sigue
  en `updateUser`; rama mock para agentes no-studio; 404 propagado sin mutar + refetch.
- Gates: `lint` 0/2, `test` 345 (47 files), `build` OK, i18n 1702/1702.
