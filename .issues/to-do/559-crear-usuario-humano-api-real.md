# Issue #559: Crear usuario humano desde el modal contra la API real (PG normalizado)

## Description

El modal "Nuevo usuario" de la vista de Usuarios (`CreateUserModal`, pestaña Humano) emite
`{username, email, role, type:'human', avatar, skills}` → `POST /users`. En modo real hoy es
**ROTO**:

1. **500**: `create_user` hace `UserRole(body.role)` (`routers/user.py:161`) y el enum del
   dominio solo admite `ADMIN|DEVELOPER|VIEWER` (`entities.py:39`), pero el select del modal
   envía vocabulario del mock (`lead-developer`, `developer`, `designer`, `manager`, `qa`) y el
   default del schema es `"developer"` (`schemas.py:943`) → `ValueError` → 500.
2. `UserCreateRequest` **descarta** `type/avatar/skills` (pydantic ignora extras) → el usuario
   nace sin perfil.
3. `usersStore.createUser` empuja la **respuesta cruda** (`UserResponse` sin `type/avatar`) →
   la tarjeta recién creada sale con badge "IA", sin botones y fecha inválida (regresión del
   síntoma de #556 justo tras crear).
4. El usuario no puede iniciar sesión (sin credencial) — eso lo resuelve **#563** por separado;
   aquí se crea con `human_user.password_hash=''` (sin login, patrón de #558).

Con el esquema normalizado de **#558**, el alta toca **3 tablas**: `users` (identidad),
`human_user` (perfil+rol+credencial) y `user_skills`/`skills` (habilidades).

Mock de referencia (`mockApi.createUser` + `users.json`): crea el usuario con el payload
completo (type, avatar, skills, role) y aparece en la lista tal cual.

## Status: TODO

## Priority: HIGH

## Component
Fullstack (Backend /users + modal + store)

## Type
feat / fullstack

## Implementation
1. **Backend — schema**: ampliar `UserCreateRequest` con `type: str = "human"`,
   `avatar: str | None`, `skills: list[str] = []`, `model: str | None`,
   `specialization: str | None`, `is_active: bool = True`. **Validación de rol estricta**:
   `role` debe existir en la tabla `roles` (`ADMIN|DEVELOPER|VIEWER` sembrados en #558) →
   `422` con `detail` claro si no (la raíz guarda `human_user.role_id` FK; el vocabulario mock
   es display y el select cambia por modo, ver 3).
2. **Backend — alta en 3 tablas** (repo de #558, transacción):
   - `INSERT INTO users` **sin `id`** (uid generado por PG, `RETURNING id`), `user_type='human'`.
   - `INSERT INTO human_user` (email, `password_hash=''` sin credencial hasta #563, `role_id`
     validado, avatar, is_active).
   - `skills`: upsert en `skills` (slug derivado del nombre) + filas en `user_skills`.
   - Unicidad: username en `users` **o** email en `human_user` → **409
     `detail="username already exists"` / `"email already exists"`** (no 500).
   - Respuesta = JOIN completo (`UserResponse` ampliada de #558). Proyección Neo4j
     `MERGE (:User {id: <uid>})` best-effort para las futuras relaciones de #569.
3. **Frontend — select por modo**: `CreateUserModal` ofrece el vocabulario del mock en mock y
   `ADMIN|DEVELOPER|VIEWER` en real (`isMockMode()`; labels con `users.adminRole/users.developer/
   users.viewerRole` ya existentes #556).
4. **Frontend — respuesta normalizada**: `usersApi.createUser` aplica `normalizeBackendUser`
   antes de devolver → la tarjeta nace con badge Humano, avatar, skills y botones.
5. **Frontend — errores**: 409 → toast con claves `users.usernameTaken`/`users.emailTaken`
   (EN/ES, según `detail`); 422 de rol → `common.error` con detalle del backend.
6. **Tests** (obligatorios):
   - Backend: `test_create_user_201_returns_uid_and_profile` (fila en `users` **y**
     `human_user`, uid de PG), `test_create_user_persists_skills_in_user_skills`,
     `test_create_user_duplicate_username_409`, `test_create_user_duplicate_email_409`,
     `test_create_user_invalid_role_422` (repo fake o PG real, patrón de
     `test_users_api.py` de #556).
   - Frontend: `usersApi.spec.ts` — `createUser` normaliza la respuesta (payload completo →
     `type:'human'`, avatar/skills preservados) y propaga 409.

## Acceptance Criteria
- [ ] `POST /users` crea `users` + `human_user` + `user_skills` con uid generado por PG y
      devuelve 201 con la fila compuesta completa
- [ ] Rol inválido → **422**; username o email duplicado → **409** (nunca 500)
- [ ] El select del modal muestra `ADMIN/DEVELOPER/VIEWER` en modo real y el vocabulario mock
      en mock
- [ ] Tras crear, la tarjeta muestra badge Humano, avatar y skills reales (respuesta
      normalizada)
- [ ] **Tests**: los 5 backend + 2 frontend listados pasan
- [ ] Gates: backend `ruff` 1011 / `mypy` 1153 / `pytest` 1331+3; frontend `lint` 0/2 /
      `test` 306 (44) / `build` OK / i18n 1693+2 (`users.usernameTaken`, `users.emailTaken`)
      EN/ES

## Files to Create
- (ninguno nuevo obligatorio; specs pueden ampliar los existentes)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`UserCreateRequest`)
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (`create_user` → 3 tablas,
  409/422)
- `src/socialseed_tasker/auth/user_store.py` o repo nuevo (transacción de alta)
- `frontend/src/components/users/CreateUserModal.vue` (select por modo)
- `frontend/src/api/usersApi.ts` + `usersApi.spec.ts`
- `frontend/src/locales/es.json` / `en.json`
- `tests/api/test_users_api.py`

## Notes
- Separación deliberada: la **credencial de login** es #563 (aquí `''` = sin login);
  el **selector unificado de skills** con catálogo es #572 (aquí el alta solo hace upsert
  de los nombres enviados).
- Si se decide mapear vocabulario mock en vez de 422, debe fijarse la tabla de correspondencia
  y testearla — la opción elegida por defecto es **select real en modo real + 422 estricto**.

## Related Issues
- #558 (esquema + repo), #563 (credencial temporal), #572 (catálogos skills/tools), #556
  (normalización de tarjeta), #557 (vista de login), #564 (crear agentes por
  `/agents/profiles`)
