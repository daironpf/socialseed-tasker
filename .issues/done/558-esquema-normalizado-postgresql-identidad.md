# Issue #558: Esquema normalizado en PostgreSQL — identidad raíz, catálogos y `GET /users` con joins

## Description

La vista de Usuarios necesita que los datos de cada usuario **persistan en PostgreSQL** (la base
`tasker-db-pg` ya levantada, `TASKER_DATABASE_URL`), porque **PG es la raíz de los usuarios** y
el **id generado allí (uid) es la clave canónica** con la que se indexan todos los datos del
proyecto en otras bases (Neo4j: issues `assignee`/`created_by` y proyección `(:User)`; Mongo:
`notifications.user_id`, chat).

**Decisión del usuario (reemplaza la idea de "todo en una tabla")**: modelo **normalizado con
una tabla por responsabilidad** (SOLID, limpieza y claridad — sin enredos de datos):

- catálogo de **roles** (RBAC), catálogo de **skills**, catálogo de **tools**;
- **identidad mínima** (`users`: uid, username, tipo);
- **perfil humano** aparte (`human_user`) y **perfil de agente** aparte (`agents_user`);
- **habilidades por usuario** (`user_skills`, N:M);
- **logs de sesión** (`session_logs`).

Estado actual (verificado en vivo y en código):

- PG tiene **una sola tabla** `users`: `id TEXT PK, username, username_normalized, email,
  password_hash NOT NULL, role, "type", created_at` (`auth/user_store.py:98`); `create_schema()`
  solo hace `CREATE TABLE IF NOT EXISTS` → no migra instalaciones existentes.
- **Identidad ya usa el id PG**: el JWT lleva `sub = user["id"]` de PG (`auth/tokens.py:72`)
  y notificaciones/chat derivan su `user_id` del `sub`. **Excepto la vista**, que lee
  **Neo4j** (`GET /users`) con ids distintos (en vivo: admin PG `id='admin'` vs nodo Neo4j
  `f5dcf582-0cd2-48e6-a900-69d8bb3c5cda`).
- `POST /users` → 500 (`UserRole("developer")`), PUT descarta `avatar/skills`, DELETE no borra
  la fila PG → todos esos arreglos (#559/#560/#562) **dependen de este esquema**.
- Frontend hay **2 listas de tools divergentes** (9 `AGENT_TOOLS` en `types/agentStudio.ts`
  vs 8 de `EditAgentModal.vue:306`) → catálogo `tools` como fuente única (#572).

Mock de referencia (`frontend/dataset-de-pruebas/users.json`): `id, username, email, role,
type (human|agent), avatar, created_at, last_active, issues_assigned, issues_created, skills[]`
y en agentes `model, specialization` — el endpoint real debe poder devolver esos campos desde PG.

Origen: vista maquetada `UsersView` + restricciones del usuario (PG raíz + tablas por
funcionalidad).

## Status: DONE (2026-10-07)

**Resolución (2026-10-07):** Implementado. DDL de **8 tablas** en `auth/user_store.py`
(`roles`/`skills`/`tools` con seeds — roles ADMIN/DEVELOPER/VIEWER con `permissions '[]'`
(permisos derivados en runtime), tools = unión **14 snake_case** de `AGENT_TOOLS` +
`EditAgentModal`; raíz `users` con `DEFAULT gen_random_uuid()::text`; split
`human_user`/`agents_user`; `user_skills` N:M; `session_logs` + 4 índices) + migración
legacy idempotente (detección `to_regclass` + `information_schema`, rename a
`users_legacy` con sufix `_2`, preservación de ids — JWT `sub` inmutable —, mapeo
`role→role_id`/`user_type`, fila `session_logs` sintética desde `last_login` legacy,
`_verify_migration` que aborta si hay desfase). Nuevo
`infrastructure/pg_user_repository.py` con JOINs (`human_user|agents_user→roles→
user_skills→skills`, role `'ai-agent'` para agentes). Router `user.py` lee PG (503 sin
`TASKER_DATABASE_URL`, 404 desconocido, DELETE con borrado PG best-effort);
`UserResponse` ampliado; `User.id: UUID|str` con coerción; lifespan `create_schema()`
siempre + re-key Neo4j (`REKEY_USER_IDS` por username); `usersApi` preserva el payload
completo y `role:null`→`ai-agent`.

**Verificación:** `pytest` **1396 passed** (+65 nuevos) + mismos 3 preexistentes;
`mypy` **1152** = HEAD; `ruff` **1334** < HEAD 1344 (0 en ficheros tocados); frontend
`lint` 0/2, `test` **308** (+2), `build` OK, i18n **1693/1693**; **33/33 checks contra
PostgreSQL real** (docker efímero): migración ×2, ids intactos, backup, seeds, FKs
CASCADE, uid `RETURNING`, login JOIN, seed dataset idempotente, JOINs de lectura,
`last_login` derivado, cascada delete.

## Priority: HIGH

## Component
Backend / Data / PostgreSQL

## Type
feat / backend

## Implementation
1. **DDL normalizado** (reemplaza el `create_schema` actual; todo idempotente con
   `CREATE TABLE IF NOT EXISTS` / `ALTER … IF NOT EXISTS`):

   ```sql
   -- Catálogo de roles (referencia inmutable de RBAC)
   CREATE TABLE IF NOT EXISTS roles (
     id          TEXT PRIMARY KEY,          -- 'ADMIN' | 'DEVELOPER' | 'VIEWER'
     name        TEXT NOT NULL,
     rank        INT NOT NULL,              -- ADMIN(3) > DEVELOPER(2) > VIEWER(1)
     permissions JSONB NOT NULL DEFAULT '[]'
   );  -- + seed INSERT … ON CONFLICT (id) DO NOTHING

   -- Catálogo de habilidades (fuente única de skills)
   CREATE TABLE IF NOT EXISTS skills (
     id   TEXT PRIMARY KEY,                 -- slug: 'vue', 'python'
     name TEXT NOT NULL UNIQUE
   );

   -- Catálogo de tools de agente (unifica AGENT_TOOLS y EditAgentModal)
   CREATE TABLE IF NOT EXISTS tools (
     id          TEXT PRIMARY KEY,          -- slug: 'code_search'
     name        TEXT NOT NULL,
     description TEXT
   );  -- + seed con la unión de las 2 listas del frontend

   -- RAÍZ: identidad mínima — uid canónico
   CREATE TABLE IF NOT EXISTS users (
     id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
     username            TEXT NOT NULL UNIQUE,
     username_normalized TEXT NOT NULL UNIQUE,
     user_type           TEXT NOT NULL CHECK (user_type IN ('human','agent')),
     created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
   );
   CREATE INDEX IF NOT EXISTS ix_users_user_type ON users (user_type);

   -- Perfil humano (1:1, cascade)
   CREATE TABLE IF NOT EXISTS human_user (
     user_id       TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
     email         TEXT UNIQUE,
     password_hash TEXT NOT NULL DEFAULT '',
     role_id       TEXT NOT NULL REFERENCES roles(id),
     avatar        TEXT,
     github_handle TEXT,
     preferences   TEXT,
     is_active     BOOLEAN NOT NULL DEFAULT TRUE
   );
   CREATE INDEX IF NOT EXISTS ix_human_user_role ON human_user (role_id);

   -- Perfil de agente (1:1, cascade) — sin role_id (los roles son de RBAC humano)
   CREATE TABLE IF NOT EXISTS agents_user (
     user_id        TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
     email          TEXT,
     avatar         TEXT,
     model          TEXT,
     specialization TEXT,
     temperature    DOUBLE PRECISION,
     system_prompt  TEXT,
     tools          JSONB NOT NULL DEFAULT '[]',  -- slugs validados contra catálogo tools
     write_access   JSONB NOT NULL DEFAULT '[]',
     limits         JSONB,
     enabled        BOOLEAN NOT NULL DEFAULT TRUE,
     last_used_at   TIMESTAMPTZ
   );

   -- Habilidades del usuario (N:M, cascade en ambos lados)
   CREATE TABLE IF NOT EXISTS user_skills (
     user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
     PRIMARY KEY (user_id, skill_id)
   );
   CREATE INDEX IF NOT EXISTS ix_user_skills_skill ON user_skills (skill_id);

   -- Log de sesiones (auditoría; DDL aquí, escritura en #571)
   CREATE TABLE IF NOT EXISTS session_logs (
     id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
     user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     event      TEXT NOT NULL CHECK (event IN ('login','logout')),
     created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     ip         TEXT,
     user_agent TEXT
   );
   CREATE INDEX IF NOT EXISTS ix_session_logs_user_created ON session_logs (user_id, created_at DESC);
   ```

2. **Migración idempotente desde la tabla legacy** (instalaciones con la tabla `users`
   antigua): detectar columnas legacy (`to_regclass` + `information_schema`) → crear las
   nuevas tablas → copiar identidad (`id, username, username_normalized, "type"` →
   `user_type` mapeando `admin/None → human`, `agent → agent`) → perfiles (`email,
   password_hash, role → role_id` con mapeo case-insensitive `ADMIN/DEVELOPER/VIEWER` y
   fallback `DEVELOPER`; perfil → `human_user` si human, a `agents_user` si agent) → si había
   `last_login`, insertar fila sintética `session_logs(event='login', created_at=old)` →
   **renombrar la tabla vieja a `users_legacy`** (backup) y verificar conteos antes de
   descartar. Nunca reasignar los ids existentes (rompería JWT/notificaciones vivos).

3. **Repositorio con JOINs** (extender `auth/user_store.py` o nuevo módulo siguiendo su
   patrón `psycopg` + `closing(… autocommit=True)`): `list_users/get_user/get_user_by_email`
   → `users ⨝ human_user/agents_user ⨝ roles (alias display) ⨝ user_skills/skills` que
   devuelven el perfil completo; `create/update` de humanos los usan #559/#560. Tests con
   store fake (protocolo `UserSeedStore` es el precedente) o PG real.

4. **Router `/users` lee la raíz**: `list_users`, `get_user`, `get_user_by_email` pasan de
   Neo4j a PG con `UserResponse` ampliada (`type/avatar/skills/model/specialization/
   is_active/last_login/github_handle/preferences`); `last_login` se **deriva**
   (`MAX(session_logs.created_at) WHERE event='login'`); sin `TASKER_DATABASE_URL` → 503 con
   detail claro.

5. **Reconciliación de la proyección Neo4j** (índice, no raíz): re-key del nodo `(:User)`
   existente al uid PG **por username** (`f5dcf582…` → `admin`) con MERGE idempotente;
   driver fake en tests. El rol de la respuesta (`role`) sale de `roles.id` para humanos y
   `'ai-agent'` derivado del `user_type` para agentes (los agentes no tienen `role_id`).

6. **Frontend `usersApi`**: spec con payload completo del backend → `normalizeBackendUser`
   preserva valores reales sobre defaults (test explícito) y `role: null` en agentes →
   `'ai-agent'`.

7. **Tests** (obligatorios): `tests/api/test_users_api.py` — `GET /users` desde PG con perfil
   completo y **uid PG**; `GET /users/{id}` y por email (JOIN con `human_user.email`);
   `last_login` derivado de `session_logs`; 503 sin database url; migración legacy idempotente
   (correr 2 veces sin error); semillas `roles/skills/tools` presentes. Frontend:
   `usersApi.spec.ts` payload completo preservado + `role null → ai-agent`.

## Acceptance Criteria
- [x] Existen las 8 tablas normalizadas con seeds (`roles`, `skills`, `tools`) y FKs con
      `ON DELETE CASCADE` correctos (jamás CASCADE hacia `roles`/`skills` catálogo)
- [x] Instalación legacy migrada de forma idempotente (2ª corrida sin cambios); ids de usuario
      existentes intactos; backup `users_legacy`
- [x] `GET /users` responde el perfil completo compuesto por JOINs, `id` = uid PG y
      `last_login` derivado de `session_logs`
- [x] Los usuarios nuevos generan uid en PG (`gen_random_uuid()::text … RETURNING id`)
- [x] Proyección Neo4j re-keyada al uid PG de forma idempotente
- [x] Sin `TASKER_DATABASE_URL` → 503 con detail explícito
- [x] **Tests**: pytest (perfil completo, uid, last_login, 503, migración) + spec frontend
- [x] Gates backend sin regresiones: `ruff` **1334** (HEAD 1344), `mypy` **1152** (= HEAD),
      `pytest` **1396 passed** + los mismos 3 preexistentes (`test_delivery_retry`,
      `test_parse_and_index_files_calls_parser`, `test_run_graph_analysis_calls_repo`);
      gates frontend: `lint` 0/2, `test` **308 (44 files)**, `build` OK, i18n 1693/1693;
      verificación extra: **33/33** contra PostgreSQL real (docker efímero)

## Files to Create
- `src/socialseed_tasker/infrastructure/pg_user_repository.py`
- `tests/api/test_user_schema_migration.py`
- `tests/api/test_users_pg_repository.py`
- `tests/fakes/fake_pg_users.py`
- `tests/infrastructure/test_neo4j_user_repository.py`
- `.issues/done/558-esquema-normalizado-postgresql-identidad.md` - este fichero

## Files to Modify
- `src/socialseed_tasker/auth/user_store.py` (DDL normalizado + migración + JOINs)
- `src/socialseed_tasker/infrastructure/web_api/routers/user.py` (GET → PG)
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`UserResponse`)
- `src/socialseed_tasker/infrastructure/neo4j_user_repository.py` o `neo4j_queries.py`
  (re-key)
- `frontend/src/api/usersApi.ts` (si hace falta) + `usersApi.spec.ts`
- `tests/api/test_users_api.py`

## Notes
- **PG raíz ≠ borrar Neo4j/Mongo**: siguen como índices/proyecciones **indexados por el uid**
  de `users` (`assignee`/`created_by`, `notifications.user_id`, chat `sub`).
- `email` y `password_hash` viven en **`human_user`** (solo humanos inician sesión → el login
  hace JOIN; los agentes no tienen credencial). `username` único en `users`.
- **Agentes sin `role_id`**: el `'ai-agent'` del mock se deriva en el frontend por `type`;
  `roles` solo alimenta RBAC humano.
- `session_logs`: aquí solo el DDL; escribir en login y retirar el endpoint huérfano es **#571**.
- Tablas fuera de este issue por SRP: `agent_runs`/`agent_run_logs` → **#574**;
  `workflows` → **#575**.
- Los scripts de seeding (`TASKER_AUTH_SEED`, wizard de #543) deben insertar en `users` +
  `human_user` (el wizard puede pasar uid explícito para seeds deterministas).

## Related Issues
- #526 (repo PG bcrypt + tabla original), #543 (wizard `create_user`), #556 (normalización +
  guard), #559/#560 (escrituras sobre este esquema), #562 (cascada), #564 (`agents_user` +
  CRUD), #571 (`session_logs`), #572 (catálogos skills/tools en API/UI), #573 (Studio sobre
  la API), #574/#575 (tablas de ejecuciones y workflows)
