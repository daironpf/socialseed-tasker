# Issue #542: Comando `tasker setup` e inicialización del stack Docker

## Description

Al instalar Tasker vía PyPI (`pip install socialseed-tasker`) o clonar el repositorio de GitHub, el usuario debe contar con un mecanismo automatizado en CLI para orquestar la infraestructura Docker sin modificar manualmente archivos de entorno. `notas.md` plantea el comando `tasker setup`: verifica Docker/Docker Compose, genera el `.env` por defecto, levanta el stack y devuelve la URL del Setup Wizard web.

Contexto real del repo: `docker-compose.yml` hoy hardcodea todos los puertos y credenciales (sin sustitución `${...}` ni `env_file`) y en la raíz solo existe `.env.example` del CLI (no del compose); los puertos del anfitrión son API `8888` y board `19001` porque Hyper-V reserva el rango `8001–8900` (por eso el default de `notas.md` `8080` no es viable en esta máquina).

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #1 (→ #542).

## Status: TODO

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
- [ ] Ejecutar `tasker setup` desde una terminal limpia inicia todos los servicios de Docker Compose y muestra un enlace activo para ingresar al Setup Wizard Web
- [ ] Sin Docker/Docker Compose instalados el comando falla con mensaje claro (sin stacktrace) y exit code != 0
- [ ] El `.env` solo se genera si no existe, con `TASKER_INSTALLED=false` y una contraseña de Neo4j no predefinida
- [ ] `docker-compose.yml` queda parametrizado con defaults idénticos a los valores actuales (el stack de hoy sigue levantándose sin `.env`)
- [ ] `tasker setup --port <n>` refleja el puerto en el compose y en la URL de salida
- [ ] Gates backend (`ruff`/`mypy`/`pytest`) sin regresiones

## Files to Create
- `src/socialseed_tasker/cli/setup_command.py`
- `tests/cli/test_setup_command.py`

## Files to Modify
- `src/socialseed_tasker/cli/app.py` — registro del comando `setup`
- `docker-compose.yml` — sustitución `${...}` + `env_file` para `TASKER_INSTALLED`
- `.env.example` — nuevas claves (`TASKER_INSTALLED`, `FRONTEND_PORT`, `API_PORT`)

## Related Issues
- #525 (Compose PostgreSQL + Redis), #536 (servicio MongoDB), #345/#382 (`init`/`install` previos del CLI), #517 (arquitectura API real), #543 (endpoints de setup), #545 (Setup Wizard al que apunta la URL)
