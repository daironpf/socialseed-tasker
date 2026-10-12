# Issue #576: Gestión de skills de usuarios humanos — alta/baja en la ventana de edición + catálogo en PostgreSQL

## Description

La edición de un usuario humano (`EditUserModal`) permite escribir chips de skills en un
input con datalist sobre `GET /skills` (#572), pero **solo persiste como reemplazo completo
de `user_skills` dentro del `PUT /users/{id}`** (#560). Consecuencias:

- No hay forma de **agregar una skill nueva directamente desde la ventana** con la semántica
  correcta de catálogo (hoy el datalist sugiere, pero el alta ocurre "por accidente" como
  parte del replace del PUT).
- No hay forma de **quitar una asignación de forma granular** sin mandar la lista completa;
  si dos ventanas editan a la vez, el último PUT machaca el `user_skills` entero.
- El catálogo `skills` (seed de #558) no tiene endpoint de **alta explícita** — solo
  `GET /skills`.

Decisión: tablas **ya existentes** (`skills`, `user_skills` de #558; NO se crean tablas
nuevas) + **endpoints dedicados** `GET/POST /users/{id}/skills` y
`DELETE /users/{id}/skills/{skill_id}`, con la ruta `POST` en modo *find-or-create* por
nombre (crear la skill en el catálogo si no existe) — que es la puerta de "agregar una skill
nueva desde la misma ventana de agregar skill". El modal en modo real gestiona las
asignaciones directamente contra estos endpoints; el `PUT /users/{id}` deja de ser el canal
de skills en la práctica (la tarjeta y el form siguen sincronizados).

## Status: DONE

## Priority: MEDIUM

## Component
Backend / Data / PostgreSQL + frontend (modal de edición de usuario)

## Type
feat / fullstack

## Implementation

1. **Store** (`PostgresUserStore`, `auth/user_store.py`, issue #576):
   - `create_skill(name)` → slug (`skill_slug`), dup por id o name → `ValueError("skill")`,
     nombre vacío tras strip → `ValueError("name")`.
   - `list_user_skills(user_id)` → `[{user_id, skill_id, name}]` por nombre; usuario
     inexistente → `None`.
   - `add_user_skill(user_id, name)` → find-or-create del catálogo por nombre + link
     `ON CONFLICT DO NOTHING` (idempotente); usuario inexistente → `None`.
   - `remove_user_skill(user_id, skill_id)` → borra **solo** la asignación en
     `user_skills`; el catálogo `skills` es compartido y **nunca** se borra desde aquí.
2. **Schemas** (`schemas.py`): `SkillCreateRequest`, `UserSkillAssignRequest` (name 1-80),
   `UserSkillResponse {user_id, skill_id, name}`.
3. **Endpoints**:
   - `routers/user.py`: `GET /users/{user_id}/skills` (404 si el uid no existe en la raíz
     PG), `POST /users/{user_id}/skills` (201 find-or-create, 404 usuario, 422 nombre),
     `DELETE /users/{user_id}/skills/{skill_id}` (200, 404 si no hay asignación), 503 sin
     `TASKER_DATABASE_URL` (patrón de #564/#572/#575).
   - `routers/catalogs.py`: `POST /skills` (201, 409 dup, 422 nombre) — alta explícita del
     catálogo para gestión desde la UI de catálogos.
4. **Frontend**:
   - `userSkillsApi.ts` (nuevo): `fetchUserSkills` / `addUserSkill` / `removeUserSkill` con
     unwrap del envolvente `APIResponse`.
   - `EditUserModal.vue`: en **modo real** los chips se cargan de
     `GET /users/{id}/skills` al abrir, el `+` llama al POST find-or-create (acepta nombre
     nuevo: crea la skill en el catálogo y la asigna), el `×` llama al DELETE (la skill
     queda en el catálogo); busy state, errores inline (`users.skillAddError` /
     `users.skillRemoveError`) y hint (`users.skillNewHint`); el form mantiene
     `form.skills` sincronizado con los asignados para que el `PUT` del save sea inocuo.
     En **mock** se mantienen los chips locales + PUT (la colección mock es dueña de sus
     entidades).
   - i18n EN/ES: `users.skillAddError`, `users.skillRemoveError`, `users.skillNewHint`.
5. **Tests**:
   - Backend `tests/api/test_user_skills_api.py` (12): lista ordenada, 404 usuario,
     asigna existente, find-or-create del catálogo, idempotencia, 404 DELETE, 422 nombre,
     catálogo intacto tras DELETE, `POST /skills` 201/409, 503 sin database, slugs.
   - Frontend: `userSkillsApi.spec.ts` (5) + `EditUserModal.spec.ts` (6): carga al abrir,
     add (POST + cache reset), remove (DELETE por slug), error inline, modo mock sin API,
     save con los chips.

## Acceptance Criteria
- [x] `GET /users/{id}/skills` devuelve las skills asignadas del humano (404 uid
      desconocido, 503 sin database)
- [x] `POST /users/{id}/skills` asigna por nombre con find-or-create del catálogo (201;
      idempotente; 404; 422 nombre vacío)
- [x] `DELETE /users/{id}/skills/{skill_id}` quita la asignación sin tocar el catálogo
      (404 si no existe)
- [x] `POST /skills` crea la skill en el catálogo (201; 409 duplicado; 422)
- [x] El modal de edición en modo real agrega una skill nueva desde la misma ventana (el
      nombre no listado se crea en el catálogo) y la asigna al instante
- [x] El modal quita skills de forma granular con `×` (sin reemplazo completo del PUT)
- [x] Modo mock intacto (chips locales, sin llamadas a los endpoints nuevos)
- [x] i18n EN+ES de los textos nuevos
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas, frontend lint/test/build,
      paridad i18n

## Resolution

Implementado el 2026-10-11. Backend: store + schemas + 4 endpoints (3 en `user.py`, 1 en
`catalogs.py`) + `tests/api/test_user_skills_api.py` (12 tests, `FakePgCursor` extendido con
handlers de skills). Frontend: `userSkillsApi.ts` (+ spec), gestión directa en
`EditUserModal.vue` (real: GET/POST/DELETE; mock: local), 3 claves i18n EN/ES (+ spec).
Gates: pytest 1503 passed + 3 preexistentes; frontend 427/57 tests, lint 0/2, build OK,
i18n 1751/1751; ruff/mypy sin delta.

Follow-ups (2026-10-12):
- **UX del picker**: el `<datalist>` nativo no se abría al pulsar `+` (solo al escribir en
  el input) → sustituido por **chips visibles y clicables** del catálogo en
  `CreateUserModal` y `EditUserModal` (real: `GET /skills`, hasta 12, filtra al escribir y
  excluye asignadas; mock: vocabulario derivado de los usuarios del dataset; nueva clave
  `users.skillSuggestions`).
- **Seed del catálogo**: `SKILLS_SEED` (10 skills: Python, TypeScript, Vue, Docker,
  PostgreSQL, Neo4j, Git, Testing, CI/CD, Kubernetes) insertado en `create_schema()`
  con `ON CONFLICT DO NOTHING` → el picker abre con opciones en base fresca
  (`test_seeds_the_skills_catalog_with_the_starter_vocabulary`).

Commit base: `4af67a7` (desplegado). Follow-ups pendientes de commit + despliegue
(esperando `si`).
