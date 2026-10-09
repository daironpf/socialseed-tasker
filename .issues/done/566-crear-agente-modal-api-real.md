# Issue #566: Crear agente desde el modal contra la API real (`POST /agents/profiles`)

## Description

El modal "Nuevo usuario" en modo Agente (`CreateUserModal.save()` con `type==='agent'`) emite
`{...fields, role:'ai-agent', type:'agent'}` → hoy en real cae en `POST /users`, que o lo
rechaza (422 con la validación de rol de #559) o lo crearía como fila humana. Con la decisión
**endpoint dedicado**, el alta de agentes debe ir a `POST /agents/profiles` (#564).

Además `usersStore.createAgent` no existe: solo `createUser` → la respuesta cruda/errónea
rompe la tarjeta igual que #556/#559 (badge, avatar, skills).

Mock de referencia: `mockApi.createUser` con `type:'agent'` crea la entidad y aparece en la
lista con `role:'ai-agent'`, model, specialization y skills.

## Status: DONE

## Priority: HIGH

## Component
Fullstack (modal + store + usersApi/agentProfilesApi)

## Type
feat / fullstack

## Implementation
1. **`usersStore.createAgent(data)`** (nuevo): llama `createAgentProfile()` (#565) y devuelve
   la respuesta **convertida al shape `User`** de la tarjeta (`type:'agent'`, `is_active` ←
   `enabled`, id PG, model, specialization, skills, avatar) — nunca un payload crudo.
2. **Ruta en el modal/store**: `CreateUserModal` emite según `type` — humano → `createUser`
   (#559), agente → `createAgent`; el reset del modal y los toasts de éxito/error son comunes
   (éxito `common.success`/clave existente, duplicado 409 → `users.usernameTaken`).
3. **Errores**: 409 username duplicado y 422 de payload (faltan campos requeridos como
   `model` si el modal no lo exige) → toast con `detail` del backend; 503 sin database →
   `common.error`.
4. **Credencial**: los agentes se crean **sin** `password_hash` (vacío, #564) → **no** abrir el
   diálogo de password temporal de #563 (condición `type==='agent'`).
5. **Tests** (obligatorios):
   - Frontend: spec de `usersStore.createAgent` — payload enviado alineado con
     `EditAgentModal`/`CreateUserModal` (model, specialization, skills, avatar, temperature,
     systemPrompt, tools, writeAccess, limits), respuesta convertida a `User` con
     `type:'agent'` y `id` del backend; 409 → error propagado; y spec del ramificado humano vs
     agente en `createUser`/`createAgent` según `type`.
   - Backend (si hace falta asegurar el contrato): el `test_create_agent_profile_201` de #564
     cubre el POST; aquí solo se exige que el front use ese contrato.

## Acceptance Criteria
- [x] Crear con pestaña Agente en real llama a `POST /agents/profiles` con el payload completo
      del modal y la tarjeta aparece con `type:'agent'`, model, specialization y skills
- [x] La respuesta se normaliza al shape de la vista (no crudo) — regresión de #556 evitada
- [x] El diálogo de password temporal (#563) **no** se abre al crear agentes
- [x] 409/422/503 → toast con el detalle del backend; modal se cierra solo en éxito
- [x] **Tests**: spec de `createAgent` + ramificado por tipo pasan
- [x] Gates frontend: `lint` 0/2, `test` 340 (47 files), `build` OK, i18n 1702 (+clave
      `users.deleteAgent` EN/ES, preexistente sin definir)

## Files to Create
- (posible) `frontend/src/stores/usersStore.spec.ts` (si no existe)

## Files to Modify
- `frontend/src/stores/usersStore.ts` (`createAgent`)
- `frontend/src/components/users/CreateUserModal.vue` (ramificar por `type`)
- `frontend/src/views/UsersView.vue` (handler de creación)
- `frontend/src/api/agentProfilesApi.ts` (si necesita ajustes de payload)
- specs frontend afectados

## Notes
- Relación con #565: este issue asume `agentProfilesApi.createAgentProfile` ya creado (orden
  del lote: #565 antes que #566).
- El rol del agente en la respuesta backend es `null` en PG (los agentes no tienen `role_id`,
  esquema #558) → `normalizeBackendUser` deriva `'ai-agent'` por `type`, y la tarjeta lo
  pinta como "IA" con la lógica existente. Las skills del alta van a `skills`/`user_skills`
  (upsert, #558) y las tools deben validarse contra el catálogo `tools` (#572).

## Related Issues
- #564 (endpoint), #565 (api + store de listado), #559/#563 (flujo humano paralelo),
  #556 (bug de respuesta cruda)

## Resolution

Implementado 2026-10-08 (commit pendiente de `si`):

- **`usersStore.createAgent(body)`**: en real llama `createAgentProfile()` con el payload
  snake_case del modal (`username/email/avatar/model/specialization/system_prompt/skills`;
  `''` → `null`), empuja la **respuesta normalizada** (`User` con `type:'agent'`,
  `role:'ai-agent'`, `is_active` ← `enabled`, id PG — nunca crudo, sin
  `temporary_password`) y re-lanza el error con `error` del store; en **mock** delega en
  `api.createUser({...type:'agent', role:'ai-agent'})` (la colección mock sigue siendo
  autónoma, sin llamada nueva).
- **Vista**: `createUser()` ramifica por `data.type === 'agent'` → `createAgent` (sin
  diálogo de password temporal), humano → `createUser` (#563 intacto); `showCreateModal`
  se pone a `false` **solo tras el 201** — en 409/422/503 el modal sigue abierto con sus
  toasts (`users.usernameTaken`/`users.emailTaken`, `common.error + detail` en 422,
  `common.error` en 503).
- **Modal**: `save()` ya solo emite (antes cerraba y reseteaba siempre); el form se resetea
  en `watch(show → open)` para que cada alta empiece limpio.
- **i18n**: clave `users.deleteAgent` EN/ES añadida (existía el uso en el botón de borrado
  de tarjeta IA pero no la clave — el render de agentes en tests la delataba).
- **Tests** (+6): `usersStore.spec` describe #566 (payload alineado con el modal + tarjeta
  normalizada sin campos crudos, 409 sin tocar la lista, rama mock sin tocar
  `createAgentProfile`) y `UsersView.spec` describe #566 (ramal agente → `createAgentProfile`
  con payload completo y sin diálogo temporal + cierre en éxito, 409 mantiene el modal abierto
  con toast, ramificado humano/agente por `type`).
- Gates frontend: `lint` 0/2, `test` 340 (47 files, +6), `build` OK, i18n 1702/1702.
