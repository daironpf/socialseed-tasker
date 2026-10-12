# Issue #577: Skills de agentes en tablas propias + ventana flotante de selección múltiple

## Description

Las skills de los agentes IA viajaban por las **mismas tablas que los humanos**
(`skills`/`user_skills`), así que un agente no podía llevar un *behavior* largo por skill —
campo que el usuario quiere para documentar **cómo** el agente debe aplicar cada skill — ni
había una ventana cómoda para seleccionar varias skills a la vez: el flujo era escribir
nombres de uno en uno en un input inline.

Decisión del usuario (Opción A):

- **Tablas separadas**: humanos siguen en `skills`/`user_skills` (#558/#576); agentes en
  **`agent_skills`** (`id` slug, `name`, `behavior TEXT` grande) +
  **`agent_user_skills`** (asignaciones N:M).
- **`behavior` NO se inyecta en el prompt de runtime** (Opción A) — se almacena y se
  edita desde la UI; inyectarlo en `system_prompt` queda como follow-up documentado.
- **Ventana flotante** de selección múltiple abierta por el botón `+` en
  `CreateUserModal` (pestaña humana y de agente), `EditUserModal` y `EditAgentModal`:
  overlay, buscador, checkboxes; en modo agente cada fila despliega su `behavior` y se
  puede crear una skill nueva **nombre + textarea grande** (`POST /agent-skills`).
  `EditAgentModal` pierde el input libre de skills.
- Seed de 3 agent skills de ejemplo con behavior extenso; migración idempotente que
  separa las asignaciones legadas por `user_type`.

## Status: DONE

## Priority: MEDIUM

## Component
Backend / Data / PostgreSQL + frontend (picker de skills de los modales)

## Type
feat / fullstack

## Implementation

1. **Store** (`PostgresUserStore`, `auth/user_store.py`):
   - `AGENT_SKILLS_DDL` / `AGENT_USER_SKILLS_DDL` añadidos al loop de `create_schema`
     (tras `USER_SKILLS_DDL`); `AGENT_SKILLS_SEED` (code-reviewer, docs-writer,
     security-analyst — behavior > 400 chars) con `ON CONFLICT DO NOTHING`.
   - Migración idempotente en `create_schema` (3 sentencias): copia el catálogo usado
     por agentes a `agent_skills` (`INSERT … SELECT DISTINCT ON`, behavior `''`),
     mueve las asignaciones de agentes a `agent_user_skills` (join `users` por
     `user_type='agent'`) y borra esos links legados de `user_skills` (los humanos
     no se tocan). Repetible sin duplicar filas.
   - `_load_skills`/`_write_skills` ahora operan sobre las tablas de agente;
     `upsert_profile` ramifica por `user_type` (agente → tablas propias, humano →
     `user_skills`); el wipe de `update_profile` borra `agent_user_skills`.
   - Catálogo CRUD: `list_agent_skills` / `create_agent_skill` (dup id o name →
     `ValueError("skill")`, nombre vacío → `ValueError("name")`) /
     `update_agent_skill` (rename 409, missing 404) / `delete_agent_skill`
     (cascada de asignaciones; missing 404).
   - `pg_user_repository._LIST_HEAD`: los skills de `GET /users` se leen con
     subconsulta correlacionada `CASE WHEN u.user_type='agent'` (adiós a los
     `LEFT JOIN user_skills/skills` globales).
2. **Schemas** (`schemas.py`): `AgentSkillResponse {id, name, behavior}`,
   `AgentSkillCreateRequest` (name 1–80, behavior ≤ 20000), `AgentSkillUpdateRequest`
   (opcionales).
3. **Endpoints** (router nuevo `routers/agent_skills.py`, tag `agent-skills`):
   `GET /agent-skills` (lista nombre+behavior), `POST /agent-skills` (201, 409 dup,
   422), `PUT /agent-skills/{id}` (200, 404, 409, 422), `DELETE /agent-skills/{id}`
   (200, 404), **503** sin `TASKER_DATABASE_URL` (patrón #564/#572/#576).
4. **Frontend**:
   - `agentSkillsApi.ts` (nuevo): `fetchAgentSkills` / `createAgentSkill` con unwrap.
   - `SkillPickerModal.vue` (nuevo): overlay `z-[60]` sobre los modales (`z-50`),
     buscador, checkboxes multi-selección, fila de `behavior` desplegable (modo
     agente), alta de skill agente (nombre + textarea grande → `POST /agent-skills`,
     seleccionada al instante) y nombre libre (modo humano), footer con contador +
     `Aplicar` (emite los nombres). Mock: vocabulario derivado del dataset.
   - `CreateUserModal` / `EditUserModal`: el `+` abre el picker (el input inline
     sigue permitiendo alta directa con Enter); `EditUserModal` aplica el **delta**
     granular (POST/DELETE por nombre; error inline + rebuild desde el servidor).
     `EditAgentModal`: input libre eliminado, `+` abre el picker en modo agente.
   - i18n EN/ES: bloque `skillPicker` (22 claves) + `users.addSkills` +
     `agents.addSkills`.
5. **Tests**:
   - Backend `tests/api/test_agent_skills_api.py` (11): CRUD del catálogo, seeds
     idempotentes con behavior extenso, migración del split (agente movido, humano
     intacto, repetible), perfil que lee de las tablas de agente (ignora el link
     legado), 503. Tests existentes de perfiles/repositorio actualizados al split
     (`test_agent_profiles_api`, `test_user_schema_migration`,
     `test_users_pg_repository`) + ramas nuevas en `FakePgCursor`.
   - Frontend: `agentSkillsApi.spec.ts` (3), `SkillPickerModal.spec.ts` (8),
     `EditUserModal.spec.ts` (+2: delta del picker, mock local; 3 existentes
     migrados de `+` a Enter), `CreateUserModal.spec.ts` (+1), `EditAgentModal.spec`
     (+1: sin input libre, catálogo de agente, payload con skills).

## Acceptance Criteria
- [x] `GET /agent-skills` devuelve nombre + behavior; `POST` 201/409/422; `PUT`
      200/404/409/422; `DELETE` 200/404 con cascada de asignaciones; 503 sin database
- [x] Perfil de agente (`create_profile`/`update_profile`/`get_profile`) lee y escribe
      en `agent_skills`/`agent_user_skills`; el humano sigue en `skills`/`user_skills`
- [x] Migración idempotente: links legados de agentes movidos a las tablas nuevas sin
      tocar a los humanos; seeds de agent skills idempotentes
- [x] `GET /users` devuelve los skills correctos por tipo (subconsulta por `user_type`)
- [x] Ventana flotante multi-selección abierta por `+` en CreateUserModal (human y
      agente), EditUserModal y EditAgentModal (overlay, buscador, Aplicar)
- [x] Modo agente: fila con `behavior` desplegable + creación de skill con nombre y
      textarea grande desde la propia ventana; EditAgentModal sin input libre
- [x] EditUserModal aplica el delta granular (POST/DELETE solo lo que cambia)
- [x] Opción A: `behavior` almacenado pero **no** inyectado en el prompt de runtime
      (follow-up documentado)
- [x] i18n EN+ES de los textos nuevos (paridad)
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas, frontend lint/test/build,
      paridad i18n

## Resolution

Implementado el 2026-10-12. Backend: 2 DDLs + seed + migración de split + CRUD de
catálogo + router `/agent-skills` + subconsulta por tipo en el repositorio + 11 tests
nuevos y 4 tests existentes ajustados al split (`FakePgCursor` con estado
`agent_skills`/`agent_user_skills`). Frontend: `agentSkillsApi.ts` (+spec),
`SkillPickerModal.vue` (+8 specs), `+` cableado en los 3 modales (EditUser con delta
granular, EditAgent sin input libre), 24 claves i18n EN/ES. Gates: pytest **1515
passed** + 3 preexistentes + 27 skipped; frontend **445 tests / 59 files**, lint 0/2,
build OK, i18n **1776/1776**; ruff/mypy **sin delta** (83=83 / 55=55 sobre los
ficheros tocados; ficheros nuevos limpios).

Follow-up (Opción A): inyectar `behavior` en el prompt de runtime (p.ej. al montar el
contexto del agente) — pendiente de decisión.

Commit pendiente (incluye picker-chips + `SKILLS_SEED` de #576) esperando `si`.
