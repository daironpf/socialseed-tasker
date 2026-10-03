# Issue #543: Endpoints `GET /setup/status` y `POST /setup/initialize`

## Description

El backend en FastAPI debe exponer endpoints para conocer si el sistema se encuentra en estado "Pendiente de Instalación" (`TASKER_INSTALLED=false`) y procesar la carga inicial de datos cuando el usuario completa el Setup Wizard: administrador, proyecto raíz y políticas de gobernanza.

Contexto real del repo: hoy **no existe** ningún rastro de `TASKER_INSTALLED` ni de `/setup/*` (es todo verde); los usuarios viven en PostgreSQL con bcrypt (`auth/user_store.py`, #526) y como nodos `:User` en Neo4j (#260), las políticas se modelan como entidades `Policy` con `logic_definition`/`severity`/`target_scope` (`routers/policy.py`), y una env var no puede mutarse en runtime del proceso — la bandera debe persistirse en base de datos (o archivo de estado) con la env como override de arranque.

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #2 (→ #543).

## Status: TODO

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
- [ ] En un sistema nuevo `GET /api/v1/setup/status` retorna `{"installed": false, "needSetup": true}`
- [ ] `POST /api/v1/setup/initialize` crea el administrador (PG bcrypt + nodo `:User` ADMIN), el `:Project` raíz y las políticas seleccionadas/custom vinculadas al proyecto
- [ ] `admin_user` se sanitiza a minúsculas sin caracteres especiales y las credenciales vacías caen a `admin`/`admin`
- [ ] Posteriores llamadas a `GET /setup/status` devuelven `{"installed": true}`
- [ ] Si `installed == true`, `POST /setup/initialize` retorna HTTP 403
- [ ] Tests backend sin dependencias de servicios externos y gates (`ruff`/`mypy`/`pytest`) sin regresiones

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
