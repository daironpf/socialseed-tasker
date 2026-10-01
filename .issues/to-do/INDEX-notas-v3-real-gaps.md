# Notas v3 Real Gaps Backlog — Issue Index

**Source:** `notas.md` (v3 — ÉPICAS 1–6: infra auth multi-capa FastAPI + Redis + PostgreSQL, vistas de grafo e impacto, observabilidad de agentes, gobernanza/constraints, dashboard y sync, Graph RAG & MCP)
**Created:** 2026-09-29
**Status:** DONE (11/11 done: #525, #526, #527, #528, #529, #530, #531, #532, #533, #534, #535)

> `notas.md` (v3) plantea 14 issues (Issue #1–#14 repartidas en 6 épicas); el siguiente
> número libre en `.issues/done` era **#524**, por lo que se numeraron **#525–#535**
> conservando el orden y contenido del plan original. 3 issues del plan ya están
> resueltas por backlogs anteriores y no generan issue nueva (ver "Already covered").
> Al ser el primer backlog con ficheros en curso, los ficheros de issue viven en
> `.issues/to-do/` hasta que se implementan (se mueven a `.issues/done/` con
> `Status: DONE`, como en los backlogs #509–#516 y #517–#524).

---

## Issue Index

| # | Issue | Priority | Type | Status | notas.md |
|---|---|---|---|---|---|
| #525 | Docker Compose Hybrid (PostgreSQL 15 + Redis 7) | CRITICAL | infra / architecture | DONE | É1 · Issue #1 |
| #526 | Username Normalization & PostgreSQL User Seeding (bcrypt) | HIGH | feat / security | DONE | É1 · Issue #2 |
| #527 | Auth API & Redis Session Management | HIGH | feat / security | DONE | É1 · Issue #3 |
| — | Conexión de `authStore` con el backend real | — | feat / integration | NO CREADA — ya resuelta en #517/#519 | É1 · Issue #4 |
| #528 | Graph View — etiquetas explícitas de aristas | LOW | feat / visualization | DONE | É2 · Issue #5 (gap) |
| #529 | Análisis de impacto y causa raíz en modo real | HIGH | bug / integration | DONE | É2 · Issue #6 (gap) |
| #530 | Ciclo de vida `agent_working` en tiempo real | MEDIUM | feat / observability | DONE | É3 · Issue #7 (gap) |
| #531 | Checklists interactivas en la pestaña Progress | LOW | feat / ux | DONE | É3 · Issue #8 (gap) |
| — | CRUD de componentes | — | feat / crud | NO CREADA — ya resuelta en #49/#433 | É4 · Issue #9 |
| #532 | Validación de políticas en tiempo de escritura + errores HARD explícitos | HIGH | feat / governance | DONE | É4 · Issue #10 (gap) |
| #533 | Health con Redis/Postgres y tarjetas de sistema | MEDIUM | feat / infra | DONE | É5 · Issue #11 (gap) |
| — | Offline-first sync (navbar ONLINE/OFFLINE/SYNCING) | — | feat / ux | NO CREADA — ya resuelta en #515/#522 | É5 · Issue #12 |
| #534 | Graph Memory: auto-embed al cerrar + `search-similar-solutions` | MEDIUM | feat / ai infrastructure | DONE | É6 · Issue #13 (gap) |
| #535 | Servidor MCP real (stdio/HTTP) para Cursor y Claude Desktop | MEDIUM | feat / ai infrastructure | DONE | É6 · Issue #14 (gap) |

---

## Feature Summary

### ÉPICA 1 — Infraestructura y Autenticación Multi-Capa
- **#525 Compose híbrido (CRITICAL):** servicios `tasker-db-pg` (PostgreSQL 15) + `tasker-redis` (Redis 7 Alpine), env `DATABASE_URL`/`REDIS_URL`/`JWT_SECRET` (convención `TASKER_*`), healthchecks y fallback in-memory
- **#526 Users en PostgreSQL (HIGH):** `normalize_username` (`a-z`, `0-9`, `.`), seeding idempotente desde `users.json` del frontend, contraseñas bcrypt = username normalizado
- **#527 Sesiones en Redis (HIGH):** login contra hash bcrypt en PG, sesión `session:{user_id}:{session_id}` con TTL, logout que revoca, refresh que renueva

### ÉPICA 2 — Vistas de Grafo e Inteligencia de Impacto
- **#528 Etiquetas de aristas (LOW):** `DEPENDS_ON`/`BLOCKS`/`AFFECTS`/`BELONGS_TO` visibles con toggle
- **#529 Análisis real (HIGH):** frontend alineado a `/analyze/*`, endpoint `/test-failures`, risk badges desde respuesta real (hoy: 404 en modo real)

### ÉPICA 3 — Observabilidad de Agentes de IA
- **#530 `agent_working` en vivo (MEDIUM):** endpoints `start-agent`/`stop-agent`, broadcast SSE de issues (`GET /issues/stream`), UI suscrita y kill switch en endpoints dedicados
- **#531 Checklist interactiva (LOW):** TODOs clicables, persistidos y en tiempo real (hoy: checkboxes deshabilitados)

### ÉPICA 4 — Gobernanza y Reglas Arquitectónicas
- **#532 Escritura protegida (HIGH):** `max_depth` aplicado al crear dependencias (409) + error `HARD` explícito en el modal de relaciones

### ÉPICA 5 — Dashboard, Sincronización y Resiliencia
- **#533 Health + Redis/Postgres (MEDIUM):** `/health` con las 3 dependencias y tarjetas en el System Dashboard (hoy: solo Neo4j)

### ÉPICA 6 — Funcionalidades Empresariales (Graph RAG & MCP)
- **#534 Graph Memory (MEDIUM):** embed automático al cerrar + `POST /ai/search-similar-solutions`
- **#535 MCP server real (MEDIUM):** transporte MCP (HTTP/stdio) con tools sobre el grafo, config para Cursor/Claude Desktop

---

## Already covered (sin issue nueva)

| notas.md | Resuelta en | Detalle |
|---|---|---|
| É1 · Issue #4 — authStore → backend real | #517, #519 | data source real, interceptor 401 → auto-refresh, LoginScreen OAuth/API key |
| É4 · Issue #9 — CRUD de componentes | #49, #433 | búsqueda por nombre/alias/UUID, detalle con issues `BELONGS_TO` |
| É5 · Issue #12 — offline-first sync | #499, #515, #522 | SyncStatusBadge ONLINE/OFFLINE/SYNCING + SyncQueueDrawer + flush hacia GitHub |

---

## Dependencies (suggested order)

1. **#525** (CRITICAL) — servicios base; desbloquea #526 → #527 → #533
2. **#526, #527** (HIGH) — auth multi-capa sobre PostgreSQL + Redis
3. **#532** (HIGH) — contratos backend↔frontend en modo real
4. **#530, #533, #534, #535** (MEDIUM) — #533 requiere #525; el resto independiente
5. **#528, #531** (LOW) — polish de UI, en cualquier momento (#531 se beneficia del broadcast de #530)

---

## Related Done Issues

| Done | Relevant to |
|---|---|
| #304, #305, #311, #425 | Redis/infra → #525/#527 |
| #69, #107, #122, #155, #162, #260, #519 | Auth/users → #526/#527 |
| #53, #80, #480–#482, #511, #517 | Graph → #528 |
| #68, #74, #100, #114, #216, #23 | Analysis → #529 |
| #81, #474, #503, #59, #504, #517 | Agent lifecycle/realtime → #530 |
| #78, #210, #469, #502 | Progress/reasoning → #531 |
| #84, #82, #85, #110, #126, #501 | Policies/constraints → #532 |
| #66, #72, #402, #407 | Health/dashboard → #533 |
| #192, #209, #228, #301, #524 | RAG/embeddings → #534 |
| #488, #524, #487, #472 | MCP → #535 |

---

## Release Checklist (backlog)

- [x] **#525** implemented — move to `.issues/done/`, `features.md` §1
- [x] **#526** implemented — move to `.issues/done/`, `features.md` §2
- [x] **#527** implemented — move to `.issues/done/`, `features.md` §2/§64
- [x] **#528** implemented — move to `.issues/done/`, `features.md` §12
- [x] **#529** implemented — move to `.issues/done/`, `features.md` §13
- [x] **#530** implemented — move to `.issues/done/`, `features.md` §18/§43
- [x] **#531** implemented — move to `.issues/done/`, `features.md` §7
- [x] **#532** implemented — move to `.issues/done/`, `features.md` §10
- [x] **#533** implemented — move to `.issues/done/`, `features.md` §14
- [x] **#534** implemented — move to `.issues/done/`, `features.md` §68/§50
- [x] **#535** implemented — move to `.issues/done/`, `features.md` §68/§50
- [x] Each issue: gates en baseline (`ruff`/`mypy`/`pytest`, `lint`/`test`/`build`), i18n EN+ES si aplica UI
- [x] Move issue file to `.issues/done/` with `Status: DONE` when complete
- [x] Commit message references `#NNN`
