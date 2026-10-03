# Issue #543: Endpoints `GET /setup/status` y `POST /setup/initialize`

## Description

El backend en FastAPI debe exponer endpoints para conocer si el sistema se encuentra en estado "Pendiente de Instalación" (`TASKER_INSTALLED=false`) y procesar la carga inicial de datos cuando el usuario completa el Setup Wizard: administrador, proyecto raíz y políticas de gobernanza.

Contexto real del repo: hoy **no existe** ningún rastro de `TASKER_INSTALLED` ni de `/setup/*` (es todo verde); los usuarios viven en PostgreSQL con bcrypt (`auth/user_store.py`, #526) y como nodos `:User` en Neo4j (#260), las políticas se modelan como entidades `Policy` con `logic_definition`/`severity`/`target_scope` (`routers/policy.py`), y una env var no puede mutarse en runtime del proceso — la bandera debe persistirse en base de datos (o archivo de estado) con la env como override de arranque.

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #2 (→ #543).

## Status: DONE (2026-10-03)

## Priority: CRITICAL

## Component
Backend / API / Setup

## Type
feat / backend

## Implementation
1. **Router `setup.py`:** nuevo router bajo `/api/v1/setup/*` con el envelope `APIResponse` (camelCase) y el guard de autenticación existente; registro en `routers/__init__.py`, `web_api/routes.py` y `app.py` (patrón de `chat.py`/`mcp.py`).
2. **`GET /setup/status`:** retorna `{"installed": bool, "needSetup": bool}`; fuente de verdad = existencia del nodo raíz de proyecto inicializado en Neo4j (o archivo de estado persistido) **o** la env `TASKER_INSTALLED=true` como override de arranque; degradación segura si Neo4j no responde (status con `installed` según env).
3. **`POST /setup/initialize`:** payload tipado en Pydantic (`SetupPayload`: `admin_user`, `admin_password`, `project_name`, `project_summary`, `policies[]`, `custom_policies[]`) con validaciones.
4. **Sanitización:** `admin_user` a minúsculas reutilizando `normalize_username` (#526); si no se envían credenciales → `admin`/`admin` por defecto.
5. **Persistencia:**
   * Admin en **PostgreSQL** con hash bcrypt (hoy `user_store` solo tiene `seed_users` → añadir `create_user`/upsert idempotente) **y** nodo `:User {username, role: 'ADMIN'}` en Neo4j.
   * Nodo `:Project {name, summary, initialized_at: datetime()}`.
   * Políticas seleccionadas y personalizadas persistidas como nodos de gobernanza conectados al proyecto con `[:APPLIES_POLICY]`, alineadas al modelo `Policy` existente (las predefinidas mapean a `logic_definition` conocidos: prevenir dependencias circulares, exigir resumen de solución; las custom como reglas libres).
6. **Bandera instalado:** persistir `TASKER_INSTALLED=true` en la fuente de verdad (BD/estado) tras inicializar; posteriores `GET /setup/status` retornan `installed: true`.
7. **Idempotencia:** si el sistema ya está instalado, `POST /setup/initialize` retorna **403 Forbidden**.
8. **Tests:** `tests/api/test_setup_endpoints.py` con Neo4j/repositorios fake (sin containers ni red), patrón de `test_chat_endpoints.py`.

## Acceptance Criteria
- [x] En un sistema nuevo `GET /api/v1/setup/status` retorna `{"installed": false, "needSetup": true}`
- [x] `POST /api/v1/setup/initialize` crea el administrador (PG bcrypt + nodo `:User` ADMIN), el `:Project` raíz y las políticas seleccionadas/custom vinculadas al proyecto
- [x] `admin_user` se sanitiza a minúsculas sin caracteres especiales y las credenciales vacías caen a `admin`/`admin`
- [x] Posteriores llamadas a `GET /setup/status` devuelven `{"installed": true}`
- [x] Si `installed == true`, `POST /setup/initialize` retorna HTTP 403
- [x] Tests backend sin dependencias de servicios externos y gates (`ruff`/`mypy`/`pytest`) sin regresiones

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/routers/setup.py`
- `tests/api/test_setup_endpoints.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/__init__.py` — exportación del router
- `src/socialseed_tasker/infrastructure/web_api/routes.py` — registro bajo `/api/v1`
- `src/socialseed_tasker/infrastructure/web_api/app.py` — persistencia de la bandera de instalación
- `src/socialseed_tasker/auth/user_store.py` — `create_user`/upsert con bcrypt

## Related Issues
- #526/#527 (usuarios PG, bcrypt, sesiones), #260 (repositorio de usuarios en Neo4j), #509/#246 (organizaciones/proyectos), #501/#82 (políticas de gobernanza), #542 (CLI que inyecta `TASKER_INSTALLED`), #544 (guard que consume `/setup/status`)

## Verification (2026-10-03)

**Implementación:** nuevo `src/socialseed_tasker/infrastructure/web_api/routers/setup.py` (`setup_router`, `Neo4jSetupStore` + Protocol `SetupStore`, `SetupStoreError`, `PREDEFINED_POLICIES`, `SetupStatusResponse`/`SetupPayload`/`SetupInitializeResponse`), `create_user()` idempotente con bcrypt en `auth/user_store.py`, registro en `routers/__init__.py`, `web_api/routes.py` y `web_api/app.py`, tests en `tests/api/test_setup_endpoints.py`.

**Gates (backend, sin regresiones):**
- `ruff check src/` → **1011** errores (baseline 1011; `routers/setup.py` y `user_store.py` a 0)
- `mypy src/` → **1153** errores / 134 ficheros; diff A/B contra HEAD (cambios en stash) = **mismo set de errores**, solo line-shift en `app.py` (+4 líneas); 0 regresiones
- `pytest -q` → **1271 passed / 27 skipped / 3 failed** (los 3 preexistentes de HEAD: `test_delivery_retry` + 2× `test_tasks_unit`); 11/11 tests nuevos de `tests/api/test_setup_endpoints.py`

**Smoke live (stack Docker, API `127.0.0.1:8888`, `TASKER_AUTH_ENABLED=true`):**
- Rebuild de `tasker-api` (src va horneado en la imagen) y contenedor healthy
- `GET /api/v1/setup/status` **sin API key** → 200 `{"installed": false, "needSetup": true}` (exención del middleware de auth)
- `POST /setup/initialize` con policy desconocida → 400 `Unknown policy`
- `POST /setup/initialize` válido → 200: `admin_user` sanitizado a `admin.review`, password vacío → fallback, `credentials:"created"` (fila PG con bcrypt), `projectId`, 4 políticas persistidas
- `POST /auth/login` con `admin.review`/`admin` → 200 JWT rol `ADMIN` (bcrypt end-to-end)
- Neo4j verificado con `cypher-shell`: `:Project Review543` con `initialized_at`, `:User admin.review` role `ADMIN`, 4 `(Project)-[:ENFORCES]->(Policy)`
- `GET /setup/status` → `{"installed": true, "needSetup": false}`; segundo `POST initialize` → **403**
- Post-smoke: reset del stack (borrado del proyecto/políticas/usuario creado en Neo4j y de la fila PG) → status final `{"installed": false, "needSetup": true}` (estado virgen para #544–#546)

**Decisiones / desviaciones respecto al texto de la issue:**
- `[:APPLIES_POLICY]` no existe en el repo; se usan nodos `:Policy` + `(Project)-[:ENFORCES]->(Policy)` (el modelo real de `routers/policy.py`), cumpliendo "alineadas al modelo `Policy` existente"
- Exención del auth middleware para `path.startswith("/api/v1/setup/")` en `app.py` (chicken-egg: el wizard no existe admin ni JWT)
- Fuente de verdad `installed`: `:Project.initialized_at` en Neo4j **o** env `TASKER_INSTALLED=true` como override de arranque (solo si es `true`; `false` no pisa la BD); si Neo4j no responde degrada solo a env
- Re-export explícito `setup_router as setup_router` en `routers/__init__.py` y `routes.py` (patrón `chat_router`/`mcp_router`) para no sumar errores `attr-defined` de `no_implicit_reexport`
- Payload acepta `policies[]` (claves `prevent_circular_dependencies`, `require_solution_summary`, `require_human_approval_core`) y `custom_policies[]` (strings libres, name truncado a 100)
