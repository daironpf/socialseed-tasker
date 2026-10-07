# Issue #560: Editar usuario humano desde el modal contra la API real (PG normalizado)

## Description

`EditUserModal` (Editar usuario de la tarjeta) emite `{...user, username, email, role, avatar,
skills}` → `PUT /users/{id}`. En modo real está **ROTO**:

1. `UserUpdateRequest` solo acepta `username/email/role/github_handle/preferences`
   (`schemas.py:948`) → **`avatar` y `skills` se descartan silenciosamente**.
2. Rol del vocabulario mock (`lead-developer`…) → sin validación → 500 al releer
   (`_node_to_user` `UserRole(...)`); con #558 la lectura es PG con `role_id` FK, pero la
   validación sigue sin existir.
3. `usersStore.updateUser` empuja la **respuesta cruda** (`UserResponse` sin `type/avatar/
   skills`) → **tras guardar, la tarjeta pierde el badge, el avatar y los botones** (regresión
   directa del síntoma #556).
4. Storage actual: Neo4j; con #558 la raíz es PG con esquema normalizado → el PUT se reparte
   en `users` (username/normalized), `human_user` (email, role_id, avatar, preferences,
   github_handle, is_active) y `user_skills` (reemplazo de habilidades).

Mock de referencia (`mockApi.updateUser` → `PUT /mock/users/:id`): devuelve la entidad
completa actualizada y la tarjeta se re-renderiza intacta.

## Status: TODO

## Priority: HIGH

## Component
Fullstack (Backend /users + modal + store + UsersView)

## Type
feat / fullstack

## Implementation
1. **Backend — schema**: ampliar `UserUpdateRequest` con `avatar`, `skills: list[str]`,
   `type`, `model`, `specialization`, `is_active` (opcionales). Validar `role` contra la tabla
   `roles` → **422** si no existe; `username` nuevo → actualizar `users.username` +
   `username_normalized` y traducir duplicado a **409**; email nuevo → unicidad en
   `human_user.email` → **409**; usuario inexistente → **404**.
2. **Backend — update en 3 tablas** (transacción, repo de #558): `UPDATE users` (si cambia
   username), `UPDATE human_user` (perfil + `role_id`), `DELETE FROM user_skills WHERE
   user_id` + re-insert (upsert de `skills`), retorno vía JOIN (`RETURNING` o re-SELECT);
   sin fila → 404. Proyección Neo4j `MERGE/SET` best-effort con el mismo uid.
3. **Frontend — respuesta normalizada**: `usersApi.updateUser` aplica `normalizeBackendUser`
   → el store reemplaza la tarjeta completa (badge/avatar/skills/fechas intactos).
4. **Frontend — select de rol por modo**: `EditUserModal.visibleRoles` ofrece
   `ADMIN/DEVELOPER/VIEWER` en modo real (mismo cambio que #559 en `CreateUserModal`).
5. **Frontend — feedback**: toast `users.updated` (EN/ES) en éxito; `users.usernameTaken` /
   `users.emailTaken` en 409; `common.error` con detail en 422/404.
6. **Tests** (obligatorios):
   - Backend: `test_update_user_full_profile_persisted` (avatar/skills/rol → `human_user` +
     `user_skills` y vuelven en la respuesta), `test_update_user_invalid_role_422`,
     `test_update_user_not_found_404`, `test_update_user_duplicate_username_409`,
     `test_update_user_duplicate_email_409` (repo fake, patrón de `test_users_api.py`).
   - Frontend: `usersApi.spec.ts` — `updateUser` normaliza la respuesta (payload crudo →
     `type/avatar/skills` preservados); **`UsersView.spec.ts` nuevo** — montar la vista con
     usuarios en el store, guardar la edición de un humano y asertar que la tarjeta conserva
     `type:'human'`, avatar y los botones (regresión del bug de respuesta cruda).

## Acceptance Criteria
- [ ] `PUT /users/{id}` persiste username/normalized en `users`, perfil+rol en `human_user`
      y skills en `user_skills`; devuelve la fila compuesta completa
- [ ] 404 sin usuario, 409 username/email duplicado, 422 rol inválido (nunca 500)
- [ ] Tras guardar desde el modal, la tarjeta NO pierde badge/avatar/skills/botones
- [ ] El select de rol muestra `ADMIN/DEVELOPER/VIEWER` en modo real conservando la opción
      actual si está fuera de la lista base (#556 `visibleRoles`)
- [ ] Toast de éxito al guardar y de error con el detalle del backend en fallos
- [ ] **Tests**: los 5 backend + spec `usersApi` + `UsersView.spec.ts` pasan
- [ ] Gates: backend `ruff` 1011 / `mypy` 1153 / `pytest` 1331+3; frontend `lint` 0/2 /
      `test` 306+ (44+ files) / `build` OK / i18n 1693+1 (`users.updated`) EN/ES

## Files to Create
- `frontend/src/views/UsersView.spec.ts`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`UserUpdateRequest`)
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (`update_user` → 3 tablas)
- `src/socialseed_tasker/auth/user_store.py` o repo nuevo
- `frontend/src/api/usersApi.ts` + `usersApi.spec.ts`
- `frontend/src/components/users/EditUserModal.vue` (select por modo)
- `frontend/src/views/UsersView.vue` (toasts con detail)
- `frontend/src/locales/es.json` / `en.json`
- `tests/api/test_users_api.py`

## Notes
- El cambio de rol con **efecto RBAC real** (JWT siguiente refleje el nuevo rol) es **#561**
  — aquí se persiste/valida, no se revocan sesiones.
- El usuario editado conserva su `password_hash`: el UPDATE toca columnas de `human_user`,
  jamás reemplaza la fila.
- `skills` en el modal puede pasar a usar el catálogo de #572 (picker) sin cambiar este
  contrato (el payload sigue siendo `skills: string[]`).

## Related Issues
- #558 (esquema + repo), #559 (crear — mismas validaciones), #561 (rol efectivo), #563
  (credencial), #572 (picker de skills), #556 (bug original de tarjeta), #567 (editar
  agente, flujo paralelo)
