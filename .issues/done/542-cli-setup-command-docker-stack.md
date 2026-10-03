# Issue #542: Comando `tasker setup` e inicialización del stack Docker

## Description

Al instalar Tasker vía PyPI (`pip install socialseed-tasker`) o clonar el repositorio de GitHub, el usuario debe contar con un mecanismo automatizado en CLI para orquestar la infraestructura Docker sin modificar manualmente archivos de entorno. `notas.md` plantea el comando `tasker setup`: verifica Docker/Docker Compose, genera el `.env` por defecto, levanta el stack y devuelve la URL del Setup Wizard web.

Contexto real del repo: `docker-compose.yml` hoy hardcodea todos los puertos y credenciales (sin sustitución `${...}` ni `env_file`) y en la raíz solo existe `.env.example` del CLI (no del compose); los puertos del anfitrión son API `8888` y board `19001` porque Hyper-V reserva el rango `8001–8900` (por eso el default de `notas.md` `8080` no es viable en esta máquina).

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #1 (→ #542).

## Status: DONE (2026-10-03)

## Priority: HIGH

## Component
CLI / DevOps / Docker

## Type
feat / cli

## Implementation
1. **Punto de entrada (`cli/app.py`):** registrar `tasker setup` como comando standalone (patrón de `init`/`install`/`status` ya presentes) con las banderas `--port` (default `19001`, el puerto real del board; documentar por qué no `8080`) y `--dev`; lógica en un módulo nuevo `cli/setup_command.py`.
2. **Prerrequisitos:** detectar Docker y Docker Compose con `shutil.which` + `docker compose version` (subproceso); si faltan, abortar con salida `Rich` clara y exit code distinto de cero.
3. **Generación dinámica de `.env`:** si no existe, escribir `TASKER_INSTALLED=false`, `TASKER_NEO4J_PASSWORD` generado aleatoriamente (fallback `neoSocial`), `API_PORT=8000` y `FRONTEND_PORT=<--port>`; idempotente (nunca pisa un `.env` existente); ampliar `.env.example` con las nuevas claves.
4. **Parametrizar `docker-compose.yml`:** introducir sustitución `${VAR:-<valor_actual>}` para puertos/credenciales (los defaults deben ser idénticos a los valores de hoy para no romper el stack actual) y `env_file: .env` en `tasker-api`/`tasker-board` para inyectar `TASKER_INSTALLED` al backend.
5. **Despliegue del stack:** `docker compose up -d` por subproceso levantando los servicios existentes (`tasker-db`, `tasker-db-pg`, `tasker-redis`, `tasker-db-mongo`, `tasker-api`, `tasker-board`, `mock-api`); en `--dev` mantener el modo desarrollo (build con recarga) sin tocar el flujo productivo.
6. **Salida en terminal:** URL formateada con `Rich` → `http://localhost:<FRONTEND_PORT>/setup` (enlace al Setup Wizard de #545).

## Acceptance Criteria
- [x] Ejecutar `tasker setup` desde una terminal limpia inicia todos los servicios de Docker Compose y muestra un enlace activo para ingresar al Setup Wizard Web
- [x] Sin Docker/Docker Compose instalados el comando falla con mensaje claro (sin stacktrace) y exit code != 0
- [x] El `.env` solo se genera si no existe, con `TASKER_INSTALLED=false` y una contraseña de Neo4j no predefinida
- [x] `docker-compose.yml` queda parametrizado con defaults idénticos a los valores actuales (el stack de hoy sigue levantándose sin `.env`)
- [x] `tasker setup --port <n>` refleja el puerto en el compose y en la URL de salida
- [x] Gates backend (`ruff`/`mypy`/`pytest`) sin regresiones

## Files to Create
- `src/socialseed_tasker/cli/setup_command.py`
- `tests/cli/test_setup_command.py`

## Files to Modify
- `src/socialseed_tasker/cli/app.py` — registro del comando `setup`
- `docker-compose.yml` — sustitución `${...}` + `env_file` para `TASKER_INSTALLED`
- `.env.example` — nuevas claves (`TASKER_INSTALLED`, `FRONTEND_PORT`, `API_PORT`)

## Related Issues
- #525 (Compose PostgreSQL + Redis), #536 (servicio MongoDB), #345/#382 (`init`/`install` previos del CLI), #517 (arquitectura API real), #543 (endpoints de setup), #545 (Setup Wizard al que apunta la URL)

## Verification (2026-10-03)

**Decisiones de implementación**
- `src/socialseed_tasker/cli/setup_command.py` registrado en `cli/app.py` con el patrón `app.command(name="setup", ...)` (junto a `init`/`install`/`status`); flags `--port/-p` (default `19001`, el puerto real del board — no `8080` por Hyper-V) y `--dev`.
- Prerrequisitos: `shutil.which("docker")` + `docker compose version` (subproceso, timeout 30 s) → mensaje `Rich` claro + `typer.Exit(1)` sin stacktrace.
- Búsqueda del compose: `find_compose_file()` asciende por `parents` desde el CWD (`docker-compose.yml|yaml`, `compose.yml|yaml`); si no existe → error claro + exit 1.
- `.env` idempotente: solo se crea si no existe (nunca se modifica), con `TASKER_INSTALLED=false`, `TASKER_NEO4J_PASSWORD` aleatoria (`secrets.token_urlsafe(16)`; fallback a `neoSocial` cuando ya existe un volumen `neo4j-data`, que conserva la contraseña con la que se inicializó), `API_PORT=8888` y `FRONTEND_PORT=<--port>`; escrito con fin de línea LF.
- **Desviaciones respecto a la Implementation:** (1) `API_PORT=8888` y no `8000` — 8000 es el puerto del contenedor, el host es `8888` (Hyper-V) y escribir 8000 movía la API y rompía `TASKER_API_URL`/`init` (detectado en el smoke y restaurado); (2) en vez de `env_file:` (rompería si `.env` no existe), `docker-compose.yml` usa sustitución `${VAR:-default}` — compose lee `.env` del proyecto solo para interpolación → sin `.env` todo funciona igual y `TASKER_INSTALLED` llega a `tasker-api` vía `${TASKER_INSTALLED:-false}`.
- Parametrización con defaults idénticos a los valores actuales: `TASKER_NEO4J_PASSWORD` (en `NEO4J_AUTH` **y** en el healthcheck `cypher-shell`), `API_PORT` 8888, `FRONTEND_PORT` 19001 (+ `TASKER_FRONTEND_URL`), `TASKER_PG_PORT` 15432, `MOCK_API_PORT` 8001, `TASKER_API_KEY`, `TASKER_JWT_SECRET`, `GITHUB_WEBHOOK_SECRET`, `TASKER_INSTALLED` — verificado con `docker compose config` antes/después (la única diferencia es `TASKER_INSTALLED: "false"`).
- Si el `.env` existente define `FRONTEND_PORT`, manda ese valor (aviso si difiere de `--port`); la variable se inyecta al subproceso `docker compose up -d` con `env={**os.environ, "FRONTEND_PORT": n}`.
- `--dev` añade `--build` a `docker compose up -d` (el flujo productivo queda como `up -d` sin build); los servicios se levantan con `cwd` = directorio del compose.
- `.env.example` ampliado con la sección "DOCKER COMPOSE (tasker setup)" (`TASKER_INSTALLED`, `FRONTEND_PORT`, `API_PORT`, `TASKER_NEO4J_PASSWORD`, `TASKER_PG_PORT`, `MOCK_API_PORT`, secretos). `features.md` sin cambios: no documenta la CLI.

**Ejecución real (AC1 / AC5)**
- `tasker setup` con el stack corriendo: `.env` creado con `neoSocial` (volumen existente detectado), solo `tasker-api` recreado (nueva env `TASKER_INSTALLED`), salida `Rich` con `http://localhost:19001/setup` → `GET /setup` devuelve **200** con la SPA (la vista del wizard llega en #544/#545), exit 0; `/health` de la API **200** en `8888` y board **200** en `19001`.
- Interpolación verificada con `docker compose --env-file`: `FRONTEND_PORT=19999` → `published: "19999"` + `TASKER_FRONTEND_URL` actualizado, `API_PORT=9999` → `published: "9999"`, contraseña propagada a `NEO4J_AUTH` y al healthcheck.

**Tests (13 nuevos)** — `tests/cli/test_setup_command.py`
- Búsqueda ascendente del compose (y `None` cuando no existe); abortos sin binario `docker` y sin plugin Compose (mensaje + exit 1); `.env` con password aleatoria ≥ 16 chars distinta de `neoSocial` y sin CR; `neoSocial` cuando existe volumen; `.env` preexistente intacto; puerto efectivo (`.env` manda + aviso / flag cuando falta la clave).
- Flujo completo: `docker compose up -d` con `cwd` del compose y `FRONTEND_PORT` en el env + URL `http://localhost:19001/setup` impresa; `--dev` → `--build`; compose ausente → exit 1 sin crear `.env`; `up` con código != 0 → exit 1 sin imprimir la URL.

**Gates (baseline)**
- `ruff check src/` **1011** (sin cambios; `setup_command.py` 0 errores), `mypy src/` **1152 errores / 133 ficheros** (sin cambios), `pytest -q` **1260 passed / 27 skipped / 3 failed** = baseline 1247 + 13 nuevos, con las 3 preexistentes (`test_delivery_retry` + 2× `test_tasks_unit`).
