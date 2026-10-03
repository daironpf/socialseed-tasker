# Onboarding & Setup Wizard Backlog — Issue Index

**Source:** `notas.md` (v5 — Épica: Flow de Onboarding & Setup Wizard Empresarial, de la instalación por CLI/Docker a la configuración guiada en la UI)
**Created:** 2026-10-03
**Status:** IN PROGRESS (2/5 done: #542, #543; pending #544, #545, #546)

> `notas.md` (v5) define las issues como [Issue #1]…[Issue #5]; interpretando la carpeta
> `.issues/done/` el siguiente número libre era **#542** (máximo actual **#541**, cerrado en
> el backlog v4 de chat #536–#541), por lo que se numeraron **#542–#546** conservando el
> orden y contenido del plan original. Es el primer backlog de `notas.md` sin issue de tests
> propia: cada issue incorpora sus propios AC de gates (`ruff`/`mypy`/`pytest` y
> `lint`/`test`/`build`). Como en los backlogs anteriores, los ficheros de issue viven en
> `.issues/to-do/` hasta que se implementan (se mueven a `.issues/done/` con `Status: DONE`).
>
> **Grounding contra el código real:**
> - `docker-compose.yml` no usa sustitución `${...}` ni `env_file` y en la raíz solo hay
>   `.env.example` del CLI → #542 debe parametrizarlo; puertos reales API `8888` / board
>   `19001` (Hyper-V reserva `8001–8900`, por eso el default `8080` de `notas.md` no sirve).
> - No existe rastro de `TASKER_INSTALLED` ni `/setup/*` en el repo (todo verde); una env var
>   no puede mutar en runtime → la bandera se persiste en BD/estado (#543).
> - `user_store.py` solo expone `seed_users` (bcrypt en PostgreSQL, #526) → falta alta de
>   admin; usuarios también como nodo `:User` en Neo4j.
> - `router.beforeEach` ya hace `initSession()` + `meta.roles` (#519) → el guard de #544 se
>   encadena y se desactiva en modo mock (#517); `/` redirige a `/board`.
> - El servidor MCP real `/mcp` (#535) y `routers/secrets.py` (#97/#106) sustentan #546.

---

## Issue Index

| # | Issue | Priority | Type | Status | notas.md |
|---|---|---|---|---|---|
| #542 | Comando `tasker setup` e inicialización del stack Docker | HIGH | feat / cli | DONE (→ `.issues/done/`) | Issue #1 |
| #543 | Endpoints `GET /setup/status` y `POST /setup/initialize` | CRITICAL | feat / backend | DONE (→ `.issues/done/`) | Issue #2 |
| #544 | Navigation guard de instalación y estado `isInstalled` | HIGH | feat / integration | TODO | Issue #3 |
| #545 | Componente `SetupWizardView.vue` (asistente paso a paso) | HIGH | feat / ux | TODO | Issue #4 |
| #546 | Configuración de credenciales de IA y servidores MCP | MEDIUM | feat / enterprise | TODO | Issue #5 |

---

## Feature Summary

### CLI / DevOps
- **#542 `tasker setup` (HIGH):** chequeo Docker/Compose (`shutil.which`), `.env` idempotente con `TASKER_INSTALLED=false`, `docker-compose.yml` parametrizado con defaults actuales, `docker compose up -d` y salida `Rich` con la URL `http://localhost:<port>/setup` (`--port` default `19001`, flag `--dev`)

### Backend
- **#543 Endpoints de setup (CRITICAL):** `GET /api/v1/setup/status` → `{installed, needSetup}` (nodo raíz/estado persistido o env override) y `POST /setup/initialize` con `SetupPayload` (admin sanitizado con `normalize_username`, default `admin`/`admin`, alta en PG bcrypt + nodo `:User` ADMIN, `:Project`, políticas `[:APPLIES_POLICY]`), bandera persistida, **403 si ya instalado**, tests con fakes

### Frontend
- **#544 Guard (HIGH):** `setupApi.ts` + `uiStore.isInstalled` cacheado, `beforeEach` encadenado a `initSession()` → `/setup` si no instalado, `/board` si intenta entrar instalado, `/setup` exento de `LoginScreen`, sin guard en modo mock
- **#545 Wizard (HIGH):** ruta `/setup` fuera de la navegación + `SetupWizardView.vue` de 4 pasos (credenciales con toggle de contraseña, proyecto, 3 checkboxes de políticas + lista dinámica personalizadas, confirmación con loader → redirect `/board`), i18n EN+ES, spec vitest

### Enterprise / AI
- **#546 Credenciales IA + MCP (MEDIUM):** paso opcional del wizard con Master API Key `tasker_sk_live_...` (generada/persistida en el backend, botón copiar) y snippet listo para `.cursor/mcp.json` / `.windsurf/mcp.json` sobre el servidor MCP `/mcp` (#535) con `X-API-Key`; `mcp_port` configurable y `SetupPayload` extendido

---

## Dependencies (suggested order)

1. **#542** (HIGH) — stack arrancado con `TASKER_INSTALLED` en el entorno; desbloquea #543
2. **#543** (CRITICAL) — contrato `status`/`initialize` que consumen #544, #545 y #546
3. **#544** (HIGH) — guard que redirige a la vista que crea #545
4. **#545** (HIGH) — wizard base sobre el que se monta #546
5. **#546** (MEDIUM) — extensión opcional del wizard y del payload

---

## Related Done Issues

| Done | Relevant to |
|---|---|
| #525, #536, #285 | Compose/puertos Windows → #542 |
| #345, #382, #275 | Comandos CLI init/install/status → #542 |
| #526, #527, #260 | Usuarios PG bcrypt + nodos `:User` → #543 |
| #509, #246 | Organizaciones/proyectos (nodo raíz) → #543 |
| #501, #82, #84 | Políticas de gobernanza → #543/#545 |
| #519, #517 | Guard de rutas, `initSession`, apiMode → #544 |
| #508, #516 | UI responsive/diseño → #545 |
| #535, #97, #106, #69 | Servidor MCP, secretos, API key → #546 |
| #518 | Suite/CI frontend → gates de #544–#546 |

---

## Release Checklist (backlog)

- [x] **#542** implemented - DONE 2026-10-03 (moved to `.issues/done/`, comando `tasker setup` + `setup_command.py` + compose parametrizado `${...}` + `.env.example`, 13 tests nuevos, gates ruff 1011 / mypy 1152 / pytest 1260 sin regresión)
- [x] **#543** implemented - DONE 2026-10-03 (moved to `.issues/done/`, router `setup.py` con `GET status`/`POST initialize`, `create_user` bcrypt en `user_store`, exención middleware `/api/v1/setup/`, 11 tests nuevos, gates ruff 1011 / mypy 1153 sin regresiones / pytest 1271 + smoke live completo con reset del stack)
- [ ] **#544** implemented — move to `.issues/done/` with `Status: DONE`
- [ ] **#545** implemented — move to `.issues/done/` with `Status: DONE`
- [ ] **#546** implemented — move to `.issues/done/` with `Status: DONE`
- [ ] Each issue: gates backend (`ruff`/`mypy`/`pytest`), `lint`/`test`/`build` si aplica UI, i18n EN+ES si aplica UI
- [ ] `features.md` actualizado por issue (rutas, componentes, secciones nuevas)
- [ ] Commit message references `#NNN`
