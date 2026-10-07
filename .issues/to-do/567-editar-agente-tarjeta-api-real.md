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

## Status: TODO

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
- [ ] Editar un agente del endpoint en real hace `PUT /agents/profiles/{id}` y la tarjeta
      conserva tipo/avatar/model/skills tras guardar
- [ ] Editar un agente local `agent-studio-*` funciona sin red (localStorage) y sigue
      funcionando en mock
- [ ] Los humanos no cambian de endpoint (test de no-regresión)
- [ ] 404/409/422/503 → toast con detalle y sin mutar la tarjeta
- [ ] **Tests**: los specs de store listados pasan
- [ ] Gates frontend: `lint` 0/2, `test` 306+ (44+), `build` OK, i18n 1693+ (claves nuevas
      EN/ES solo si se añaden)

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
