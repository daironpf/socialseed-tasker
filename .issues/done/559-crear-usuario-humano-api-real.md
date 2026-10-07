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

## Status: DONE (2026-10-07)

**Resolución (2026-10-07):** Implementado. `UserCreateRequest` ampliado (`type/avatar/
skills/model/specialization/is_active`; `role` default `"developer"` validado
case-insensitive contra la tabla `roles` → **422** con el detalle de opciones;
`type != 'human'` → **422** apuntando a `/agents/profiles`). `PostgresUserStore.
create_human_user` hace la alta **transaccional** en `users` (uid `RETURNING id`) +
`human_user` (`password_hash=''` hasta #563, `role_id` FK, avatar/is_active) +
`skills`/`user_skills` (slug), con pre-checks de unicidad → `ValueError('username'|
'email')` → **409** `username/email already exists` (y `UniqueViolation` en carrera
mapeado igual); rollback en cualquier fallo (FK incluida). Router: 201 + lectura de
vuelta con el JOIN completo, proyección Neo4j best-effort `MERGE (u:User {id: <uid>})`
(`MERGE_USER` + `UserRepository.merge_user`, nodo nace con el uid PG) y 503 sin
`TASKER_DATABASE_URL`. Frontend: select de rol por modo (`isMockMode()`: mock →
vocabulario dataset, real → admin/developer/viewer con labels #556), `usersApi.createUser`
aplica `normalizeBackendUser` + `suppressErrorToast`, store re-lanza el error y
`UsersView` traduce 409 → `users.usernameTaken`/`users.emailTaken` y 422 →
`common.error` + detalle (i18n EN/ES +2 → 1695/1695).

**Verificación:** `pytest` **1405 passed** (+9: 7 POST /users + 2 merge) + mismos 3
preexistentes; `mypy` **1136** ≤ 1152 (anotado `_get_session -> Any` en el repo Neo4j);
`ruff` **1334** = estado #558 (user.py 7, tests nuevos 0); frontend `lint` 0/2,
`test` **310** (+2), `build` OK, i18n **1695/1695**; **13/13 contra PostgreSQL real**
(docker efímero): transacción 3 tablas, uid PG, skills enlazados, JOIN de lectura,
dup username/email → ValueError, FK `role_id` → rollback sin filas huérfanas,
`list_role_ids`.

**Fix posterior (mismo commit, hallazgo del smoke en despliegue):** el `POST /users`
real estaba **sombreado** — `project_router` se registra antes que `user_router`
(`app.py` 506 < 521) y su endpoint legacy de Neo4j `POST /users?project_id=` (crea
nodo y lo liga al proyecto) capturaba la petición → 422 `query.project_id`. Renombrado
el legacy a **`POST /api/v1/projects/users`** (único consumidor: `cli/init_command.py`,
actualizado) y añadido test de ruteo `test_post_users_route_is_not_shadowed_by_project_router`.
Smoke en despliegue real: **13/13** — legacy en `/projects/users` (422 sin
`project_id`), create 201 con uid PG + perfil + skills del JOIN, 409×2, 422 rol,
coherencia create↔listado, segundo create → DELETE 200 (guard Neo4j pasa con 2 nodos,
fila PG eliminada), último usuario → 409. Gates de este fix: `pytest` **1406 passed**
+ los mismos 3 preexistentes, `mypy` **1136**, `ruff` sin regresiones (project.py
20=20, init_command.py 62=62, tests 0). Nota de datos: `skills.name` en vivo es
minúsculo (seed + dataset mock) — el JOIN de `PgUserRepository` devuelve ese nombre
tal cual; sin regresión respecto a `GET /users`.

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
- [x] `POST /users` crea `users` + `human_user` + `user_skills` con uid generado por PG y
      devuelve 201 con la fila compuesta completa
- [x] Rol inválido → **422**; username o email duplicado → **409** (nunca 500)
- [x] El select del modal muestra `ADMIN/DEVELOPER/VIEWER` en modo real y el vocabulario mock
      en mock
- [x] Tras crear, la tarjeta muestra badge Humano, avatar y skills reales (respuesta
      normalizada)
- [x] **Tests**: los 5 backend + 2 frontend listados pasan
- [x] Gates: backend `ruff` **1334** (= estado #558, sin regresiones) / `mypy` **1136**
      (≤ 1152) / `pytest` **1405 passed** + los mismos 3 preexistentes (`test_delivery_retry`,
      `test_parse_and_index_files_calls_parser`, `test_run_graph_analysis_calls_repo`);
      frontend `lint` 0/2 / `test` **310 (44 files)** / `build` OK / i18n **1695/1695**
      (`users.usernameTaken`, `users.emailTaken` EN/ES); verificación extra: **13/13**
      contra PostgreSQL real (docker efímero)

## Files to Create
- (ninguno nuevo; specs ampliados en los existentes)
- `.issues/done/559-crear-usuario-humano-api-real.md` - este fichero

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
