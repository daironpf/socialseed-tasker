# Issue #556: Vista de Usuarios en modo real — normalización de la tarjeta y guard del último usuario

## Description

Reportado por el usuario: en la vista de Usuarios la tarjeta de su usuario `admin` aparece
"bloqueada" — no deja editarle nada.

Diagnóstico (verificado en vivo con `GET /api/v1/users`):

1. **El payload real no trae los campos que la vista espera.** El perfil Neo4j del admin llega
   `{"username":"admin","email":null,"role":"ADMIN","created_at":…,"last_login":null}` — sin
   `type`, `avatar`, `skills` ni `last_active` (el dominio `User` solo tiene
   username/email/role/github_handle/preferences).
2. **La vista gatea los botones por `type`:** editar/eliminar son `v-if="user.type === 'human'"`
   → con `type: undefined` **no se renderiza ningún botón** → "no me deja editar nada".
3. Síntomas adicionales: badge de la tarjeta cae a "IA", avatar vacío, "Ultima vez: Invalid Date"
   (`new Date(undefined)`), el contador "Humanos" no le cuenta, `formatRole('ADMIN')` muestra
   "ADMIN" en cruto y el select del modal no tiene opción ADMIN (quedaría en blanco).
4. Solo pasa en **modo real** (mock trae fixtures completos) — por eso aparece recién en la
   instalación nueva.

Guard de borrado (requisito del usuario: *"que el sistema no se quede sin usuario"*), con la
nota de que **existen dos tipos de usuarios** (`human` y `agent` — columna `"type"` de PG/seed
`users.json` y badges Humano/IA de la vista):

- Un guard sobre `users.length` fallaría: con `[admin(humano), agentA, agentB]` la lista nunca
  quedaría vacía pero el sistema se quedaría **sin humanos**.
- Por eso el guard mide **humanos**: `humans.length <= 1` deshabilita Eliminar en tarjetas
  humanas; los agentes se pueden borrar libremente.

## Status: DONE (2026-10-06)

## Priority: HIGH

## Component
Frontend (UsersView / usersApi / EditUserModal) + Backend (guard DELETE /users)

## Type
bug fix / UX + invariant

## Implementation
1. **`frontend/src/api/usersApi.ts` → `normalizeBackendUser`** (antes de `mergeStudioAgents`):
   rellena `type: 'human'` (los agentes entran después del studio con `type: 'agent'`),
   `avatar: '👤'`, `skills: []`, `email: ''` (acepta `null`), `issues_*: 0`,
   `last_active: last_active ?? last_login ?? created_at` e `is_active: true`. Idempotente para
   payloads mock completos.
2. **`frontend/src/views/UsersView.vue`:**
   - `formatRole` ampliado: `ADMIN`→`users.adminRole`, `VIEWER`→`users.viewerRole`,
     `DEVELOPER`→`users.developer` (además de los roles mock).
   - `isLastHuman = humans.length <= 1` → botón Eliminar humano con
     `:disabled` + `title`/`aria-label` condicionales (`users.lastUserGuard`) y
     `disabled:opacity-40 disabled:cursor-not-allowed`. Agentes sin guard.
   - `deleteUser`/`deleteAgent` ahora avisan con toast cuando el store devuelve `false`
     (el `try/catch` anterior nunca disparaba: el store no lanza).
3. **`frontend/src/components/users/EditUserModal.vue`:** `visibleRoles` añade la opción actual
   si no está en la lista base (rol `ADMIN` visible y seleccionable) + `roleLabel` con el mapa
   completo de roles.
4. **Backend `routers/user.py` → `delete_user`:** `len(repo.list_users(limit=2)) <= 1` →
   `HTTPException(409, "Cannot delete the last user")`. En Neo4j solo viven perfiles humanos
   (los agentes no están en `/users`), así que "último usuario" equivale a "último humano".
   Se eliminó el `from fastapi import HTTPException` local de la rama 503 (hacía
   `UnboundLocalError` al referenciar el import de módulo — patrón legacy del fichero).
5. **i18n es/en (+3 claves → 1693/1693):** `users.adminRole`, `users.viewerRole`,
   `users.lastUserGuard`.

## Acceptance Criteria
- [x] La tarjeta del admin en modo real muestra badge "Humano", avatar por defecto, fecha válida
      y cuenta en "Humanos"; los botones editar/eliminar se renderizan
- [x] `formatRole('ADMIN')` → "Administrador"/"Admin"; el modal muestra el rol actual sin perderlo
- [x] Con 1 solo humano, Eliminar está deshabilitado en tarjetas humanas con tooltip
      (`users.lastUserGuard`); con ≥2 humanos se habilita; los agentes no tienen guard
- [x] Backend: `DELETE /users/{id}` con el único usuario → **409** y no borra; con ≥2 → borra
- [x] Fallo de borrado (409 u otro) visible como toast (antes silencioso)
- [x] Verificación en vivo previa: payload admin real capturado y normalizado por el spec
- [x] Gates: `ruff` sin regresión (baseline 1011), `mypy` sin regresión (baseline 1153),
      `pytest` **1331 passed + 3 preexistentes** (+2 tests), `npm run lint` 0 errors/2 warnings,
      `npm test` **304 passed (44 files)** (+3 tests/+1 spec), `npm run build` OK,
      i18n EN/ES **1693/1693**

## Files to Create
- `tests/api/test_users_api.py` — 2 tests (409 último usuario / borrado con ≥2)
- `frontend/src/api/usersApi.spec.ts` — 3 tests (normalización admin, idempotencia, envelope vacío)
- `.issues/done/556-vista-usuarios-normalizacion-y-guard.md` — este fichero

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` — guard 409 + fix import local
- `frontend/src/api/usersApi.ts` — `normalizeBackendUser`
- `frontend/src/views/UsersView.vue` — formatRole, `isLastHuman`, disabled + toasts
- `frontend/src/components/users/EditUserModal.vue` — `visibleRoles` + `roleLabel`
- `frontend/src/locales/es.json` / `en.json` — 3 claves `users.*`
- `features.md` — §11
- `.issues/to-do/INDEX-notas-v6-notifications-mongodb.md` — fila + follow-up #556

## Notes
- **Dos tipos de usuario:** `human` y `agent` (columna `"type"` de la tabla PG `users`, seed
  `frontend/dataset-de-pruebas/users.json` con 3 humans + 5 agents, y `user_type="admin"` del
  wizard). El guard se diseñó sobre **humanos** precisamente por esto (ver Description.4).
- **Los agentes no viven en Neo4j:** llegan al frontend solo vía Agent Studio
  (`mergeStudioAgents`), por eso el guard genérico del backend == "último humano".
- **El login no se toca:** borrar el perfil Neo4j no afecta a las credenciales PG (el409 solo
  protege la lista de perfiles de la vista).
- **`HTTPException` y scope de función:** cualquier `from fastapi import HTTPException` dentro
  de una función hace que el nombre sea local en toda ella — el import de módulo (línea 12)
  solo funciona si se elimina el import local.

## Related Issues
- #542/#543 (setup/wizard que crea el admin), #526 (PG `users."type"` y credenciales),
  #519 (UsersView original), #554 (login con esas credenciales)
