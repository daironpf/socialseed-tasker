# INDEX — Backlog v7: Vista de Usuarios contra la API real (PostgreSQL como raíz, modelo normalizado)

**Source:** vista maquetada `frontend/src/views/UsersView.vue` + mock
`frontend/dataset-de-pruebas/users.json` / `issues.json` + restricciones del usuario
**Created:** 2026-10-07
**Status:** IN PROGRESS (11/18) — #558 DONE 2026-10-07, #559 DONE 2026-10-07, #560 DONE 2026-10-07, #561 DONE 2026-10-07, #562 DONE 2026-10-08, #563 DONE 2026-10-08, #564 DONE 2026-10-08, #565 DONE 2026-10-08, #566 DONE 2026-10-09, #567 DONE 2026-10-09, #568 DONE 2026-10-09
**Numeración:** #558–#575 (continúa tras #557 del índice v6)

---

> **Grounding (estado real verificado):**
>
> - **PostgreSQL (`tasker-db-pg`) es la raíz de los usuarios** y el **uid generado allí es la
>   clave canónica** con la que se indexan todos los datos del usuario en otras bases (Neo4j:
>   issues `assignee`/`created_by` y proyección `(:User)`; Mongo: `notifications.user_id`,
>   chat). El JWT ya usa `sub = users.id` (`auth/tokens.py:72`).
> - **Modelo normalizado (decisión del usuario — tablas por responsabilidad, SOLID, sin
>   enredos):** 11 tablas — catálogos `roles`, `skills`, `tools`; raíz `users` (uid, username,
>   `user_type human|agent`); perfiles `human_user` (email, `password_hash`, `role_id` FK,
>   avatar…) y `agents_user` (model, specialization, tools/limits JSONB…); N:M `user_skills`;
>   auditoría `session_logs`; y de otros issues `agent_runs`/`agent_run_logs` (#574) +
>   `workflows` (#575). Migración idempotente desde la tabla legacy única (backup
>   `users_legacy`); `last_login` **derivado** de `session_logs`, no columna.
> - **Fractura actual:** la vista lee `GET /users` desde **Neo4j** con uids distintos (admin PG
>   `id='admin'` vs nodo `f5dcf582-0cd2-48e6-a900-69d8bb3c5cda`) → `POST /users` → 500
>   (`UserRole("developer")`, enum solo `ADMIN|DEVELOPER|VIEWER`), PUT descarta
>   `avatar/skills` y rompe la tarjeta con la respuesta cruda, DELETE dejaba viva la fila PG
>   (guard contando en Neo4j) → corregido en #562 (guard en PG, fila raíz borrada, cascada).
> - **Colisión de rutas corregida en #559:** `project_router` se registra antes que
>   `user_router` y su endpoint legacy `POST /users?project_id=` (crea nodo Neo4j y lo liga
>   al proyecto) **sombreaba** el alta PG con un 422 `query.project_id` → renombrado a
>   **`POST /api/v1/projects/users`** (único consumidor `cli/init_command.py` actualizado) +
>   test de ruteo. El guard «último usuario» del DELETE contaba en Neo4j → corregido en #562
>   (cuenta humanos en PG).
> - **Agentes** = endpoint dedicado **`/agents/profiles`** (decisión del usuario); filas `users`
>   `user_type='agent'` sin credencial ni `role_id` (el `ai-agent` del mock se deriva en el
>   front por `type`) + `agents_user` con cascada. **Agent Studio se migra a la API en #573**
>   (antes: solo localStorage `agent-studio-v1`, contrato del prefijo `agent-studio-*`).
>   Cuidado con la colisión `/agents/profiles` vs `/agents/{agent_id}` → registrar el router
>   antes.
> - **Crear usuario genera credencial PG con password temporal visible una vez** (decisión del
>   usuario): `temporary_password` solo en la respuesta del POST en `human_user.password_hash`
>   bcrypt, login inmediato con ella — implementado en #563 (dialogo de una sola visualización).
> - **Catálogos**: `skills`/`tools` sembrados; el frontend hoy tiene **2 listas de tools
>   divergentes** (9 `AGENT_TOOLS` vs 8 de `EditAgentModal`) → `GET /tools` como fuente única
>   (#572).
> - Esquema `create_schema` es `CREATE TABLE IF NOT EXISTS` → migraciones idempotentes; uid
>   nuevo generado en PG (`DEFAULT gen_random_uuid()::text … RETURNING id`), **los ids
>   existentes no se migran**.
> - `GET /issues` con `le=100` rompe `fetchIssues(1, 200)` de la vista (422); el dominio
>   `Issue` no tiene `assignee`/`created_by` (el sí los tiene); `POST /users/{id}/last-login`
>   existe pero nadie lo llama → #569/#570/#571.
> - Workflows y logs de ejecución son **greenfield**: solo `.agent/workflows/*.md` de texto y
>   un ring buffer de logs en memoria (200/issue, se pierde al reiniciar).

---

## Issue Index

| # | Fichero | Título | Prioridad | Tipo | Depende de |
|---|---------|--------|-----------|------|------------|
| 558 | `558-esquema-normalizado-postgresql-identidad.md` | Esquema normalizado en PostgreSQL — identidad raíz, catálogos y `GET /users` con joins | HIGH | feat/backend | — |
| 559 | `559-crear-usuario-humano-api-real.md` | Crear usuario humano desde el modal contra la API real (PG normalizado) | HIGH | feat/fullstack | #558 |
| 560 | `560-editar-usuario-humano-api-real.md` | Editar usuario humano desde el modal contra la API real (PG normalizado) | HIGH | feat/fullstack | #558 |
| 561 | `561-rol-usuario-efectivo-rbac.md` | El rol editado surte efecto real en RBAC (JWT desde la raíz PG) | MEDIUM | feat/backend | #560 |
| 562 | `562-borrado-cascada-usuario-raiz.md` | Borrado raíz en cascada — eliminar usuario borra su credencial PG y sus datos indexados | HIGH | feat/backend | #558, #561 |
| 563 | `563-credencial-temporal-crear-usuario.md` | Credencial temporal al crear usuario humano (login inmediato) | MEDIUM | feat/fullstack | #559 |
| 564 | `564-agentes-user-crud-postgres.md` | CRUD de perfiles de agente en PostgreSQL — endpoint dedicado `/agents/profiles` | HIGH | feat/backend | #558 |
| 565 | `565-listado-agentes-api-real-vista.md` | Listado de agentes en la vista desde la API real (merge PG + profiles API + localStorage) | HIGH | feat/fullstack | #564 |
| 566 | `566-crear-agente-modal-api-real.md` | Crear agente desde el modal contra la API real (`POST /agents/profiles`) | HIGH | feat/fullstack | #565 |
| 567 | `567-editar-agente-tarjeta-api-real.md` | Editar agente desde la tarjeta contra la API real (`PUT /agents/profiles/{id}`) | MEDIUM | feat/fullstack | #565 |
| 568 | `568-eliminar-agente-tarjeta-api-real.md` | Eliminar agente desde la tarjeta contra la API real (`DELETE /agents/profiles/{id}`) | MEDIUM | feat/fullstack | #565 |
| 569 | `569-issues-assignee-created-by-usuario.md` | Issues con `assignee`/`created_by` indexados por el uid de `users` + endpoints por usuario | HIGH | feat/backend | #558 |
| 570 | `570-contadores-modal-issues-usuario.md` | Contadores y modal de issues por usuario en la vista | HIGH | feat/frontend | #569 |
| 571 | `571-session-logs-postgres.md` | Log de sesiones en PostgreSQL (`session_logs`) — escritura en login y `last_login` derivado | LOW | feat/backend | #558, #561 |
| 572 | `572-catalogos-skills-tools-api-ui.md` | Catálogos `GET /skills` y `GET /tools` — selector de skills y lista unificada de tools | MEDIUM | feat/fullstack | #558, #564 |
| 573 | `573-migracion-agent-studio-api.md` | Migración de Agent Studio a la API — builder sobre `/agents/profiles` | HIGH | feat/fullstack | #564, #565 |
| 574 | `574-historial-ejecuciones-agentes-logs.md` | Histórico de ejecuciones de agentes en PostgreSQL — `agent_runs` + `agent_run_logs` | MEDIUM | feat/fullstack | #564, #573 |
| 575 | `575-workflows-biblioteca-postgres.md` | Workflows en PostgreSQL — biblioteca de definiciones con importación de `.agent/workflows/*.md` | MEDIUM | feat/fullstack | #558, #573 |

---

## Feature Summary

- **Backend / PostgreSQL (raíz, modelo normalizado de 11 tablas):** DDL por responsabilidad
  (`roles`, `skills`, `tools`, `users`, `human_user`, `agents_user`, `user_skills`,
  `session_logs` en #558; `agent_runs`/`agent_run_logs` en #574; `workflows` en #575) con
  seeds, FKs `ON DELETE CASCADE` e índices; migración idempotente desde la tabla legacy;
  repositorio con JOINs; `GET/POST/PUT/DELETE /users` sobre `users`+`human_user`+
  `user_skills` (409 duplicado username/email, 409 último humano en PG, 404/422);
  revocación de sesiones al cambiar rol (`role_id` FK); borrado en cascada (credencial +
  proyección Neo4j + sesiones + `notifications` Mongo, best-effort); credencial temporal
  bcrypt en el alta; router `/agents/profiles` antes de `/agents/{agent_id}` con validación
  de tools; `GET /skills`/`GET /tools`; issues con `assignee`/`created_by` (uid) +
  `GET /users/{id}/issues?kind=` + `/issue-stats`; `session_logs` escritos en el login y
  `last_login` derivado (retirada del endpoint huérfano); runs de agentes con logs
  persistentes; workflows builtin importados de `.md` + CRUD custom con `created_by` uid.
- **Frontend (vista Usuarios + Agent Studio):** select de rol por modo (mock vs
  `ADMIN/DEVELOPER/VIEWER`); normalización de respuestas en `createUser/updateUser/
  createAgent/updateAgent` (regresión #556 evitada, `role: null` → `'ai-agent'`); diálogo de
  password temporal una sola vez; `agentProfilesApi`/`catalogsApi`/`agentRunsApi`/
  `workflowsApi` nuevos; `fetchUsers` = humanos PG + perfiles + locales `agent-studio-*` sin
  duplicados; dispatch por tipo en el store (humano → `/users`, agente →
  `/agents/profiles`, local → localStorage); contadores y modal vía endpoints por usuario
  (adiós a `fetchIssues(1,200)`); picker de skills y **lista unificada de tools** desde los
  catálogos; **Agent Studio persiste en la API** con importación única de los perfiles
  locales; pestaña de historial de ejecuciones con logs y visor de workflows.

## Dependencies (orden sugerido del lote)

```
558 ─┬─► 559 ─┬─► 563
     │        └─► 560 ─► 561 ─┐
     ├─► 562 ◄────────────────┘
     ├─► 564 ─┬─► 565 ─┬─► 566
     │        │        ├─► 567
     │        │        ├─► 568
     │        │        └─► 573 ─┬─► 574
     │        └─► 572 ◄────────┘      (575 cuelga de 558+573)
     ├─► 569 ─► 570
     ├─► 571 (tras 561)
     └─► 572 / 575
```

- Riel crítico: **#558** (esquema + `GET`) → #559/#560 → #561/#562.
- Riel de agentes: **#564** → #565 → #566/#567/#568 → **#573** → #574; #572 en paralelo.
- Riel de issues: **#569** → #570. Riel Studio/workflows: #573 → #575.
- **#563** cuelga de #559; **#571** de #558+#561; **#572/#575** de #558.

## Related Done Issues

- **#519** base de la vista Usuarios (UsersView + JWT), **#513** Agent Studio (mock, DONE),
  **#517/#472** SSE de logs (memoria), **#526** repo PG bcrypt, **#533** filtros de issues,
  **#543** wizard `create_user`, **#547–#553** notifications/chat (`user_id` = sub),
  **#554/#555** fixes previos, **#556** normalización de tarjeta + guard 409, **#557** login
  de vista limpio.

## Release Checklist

- [x] #558 esquema normalizado + `GET /users` con joins
- [x] #559 crear usuario humano
- [x] #560 editar usuario humano
- [x] #561 rol efectivo en RBAC
- [x] #562 borrado en cascada
- [x] #563 credencial temporal
- [x] #564 `/agents/profiles` CRUD
- [x] #565 listado de agentes
- [x] #566 crear agente
- [x] #567 editar agente
- [x] #568 eliminar agente
- [ ] #569 issues por uid + endpoints por usuario
- [ ] #570 contadores y modal
- [ ] #571 `session_logs` + `last_login` derivado
- [ ] #572 catálogos skills/tools
- [ ] #573 migración de Agent Studio a la API
- [ ] #574 histórico de ejecuciones (`agent_runs`/`agent_run_logs`)
- [ ] #575 workflows (biblioteca + import `.md`)
- [ ] Cada issue: gates backend (`ruff` ≤ 1334 / `mypy` ≤ 1152 / `pytest` sin nuevas
      fallas — 3 preexistentes), `lint`/`test`/`build` si aplica UI, i18n EN+ES si aplica UI
- [ ] Mover fichero a `.issues/done/` con `Status: DONE` al implementarse
- [ ] Commit message references `#NNN`
