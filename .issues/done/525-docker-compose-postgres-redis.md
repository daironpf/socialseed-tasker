# Issue #525: Docker Compose Hybrid Environment (PostgreSQL 15 + Redis 7)

## Description

`docker-compose.yml` solo orquesta Neo4j (`tasker-db`), la API (`tasker-api`), el board (`tasker-board`) y el mock (`mock-api`). La ÉPICA 1 de `notas.md` requiere una infraestructura multi-capa para autenticación y persistencia: PostgreSQL como store de usuarios/credenciales y Redis como store de sesiones y caché, relacionados con la API de FastAPI y la UI de Vue 3.

Origen: `notas.md` → ÉPICA 1 · Issue #1 (→ #525).

## Status: DONE (2026-09-29)

## Priority: CRITICAL

## Component
Infra / Docker / Auth Infrastructure

## Type
infra / architecture

## Implementation
1. **Servicio `tasker-db-pg`:** imagen `postgres:15-alpine`, variables `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB`, volumen `pg-data`, healthcheck `pg_isready -U ...`, puerto `127.0.0.1:5432` publicado solo para debugging local.
2. **Servicio `tasker-redis`:** imagen `redis:7-alpine`, healthcheck `redis-cli ping`, volumen opcional `redis-data`, puerto `127.0.0.1:6379`.
3. **Variables de entorno en `tasker-api`:** `TASKER_DATABASE_URL` (PostgreSQL), `TASKER_REDIS_URL` (`redis://tasker-redis:6379/0`) y `TASKER_JWT_SECRET` (ya existe; es el `JWT_SECRET` de `notas.md` bajo la convención `TASKER_*` del repo); `depends_on` con `condition: service_healthy` sobre ambos servicios nuevos.
4. **Reutilizar código existente:** `cli/wiring.py` ya consume `TASKER_REDIS_URL` (`RedisStorage`, `RedisRateLimiter`); exponer el mismo patrón a la capa web con fallback a in-memory cuando no haya URL (dev sin compose).
5. **Smoke:** `docker compose up -d` → todos healthy; API responde `/health`; Neo4j y mock-api intactos.

## Acceptance Criteria
- [x] `tasker-db-pg` (PostgreSQL 15) y `tasker-redis` (Redis 7 Alpine) definidos en `docker-compose.yml` con healthchecks
- [x] `DATABASE_URL`, `REDIS_URL` y `JWT_SECRET` (convención `TASKER_*`) conectan la API con la DB y Redis
- [x] Todos los contenedores arrancan con `docker compose up -d` y pasan sus healthchecks
- [x] La API degrada con fallback in-memory/in-process cuando Redis/Postgres no están configurados
- [x] Gates backend en baseline (`ruff`/`mypy`/`pytest`) sin regresiones

## Verification (2026-09-29)
- **Compose:** `tasker-db-pg` (`postgres:15-alpine`, `pg_isready`, vol `pg-data`, `127.0.0.1:15432→5432`) y `tasker-redis` (`redis:7-alpine`, `redis-cli ping`, AOF + vol `redis-data`, `127.0.0.1:6379`); `tasker-api` con `TASKER_DATABASE_URL`/`TASKER_REDIS_URL` (+ `TASKER_JWT_SECRET` ya existente) y `depends_on: service_healthy` sobre Neo4j + PG + Redis. **Desviación:** el puerto PG de host es `15432` porque el anfitrión ya tiene un Postgres nativo en el `5432` (mismo patrón que el workaround de puertos documentado en `features.md`).
- **Módulo compartido:** nuevo `src/socialseed_tasker/config/storage.py` (`get_redis_url`/`get_database_url`/`build_storage`) consumido por `cli/wiring.py` (dedupe del patrón inline) y `infrastructure/web_api/app.py` (events/session store con backend en `app.state.storage_backend` + log `event storage backend: redis`); `redis>=5.0.0` añadido a las dependencias main de `pyproject.toml` para que la imagen de la API pueda usarlo.
- **Smoke (docker compose up -d):** 6/6 contenedores healthy; `/health` → 200; dentro de `tasker-api`: `REDIS_URL`/`DATABASE_URL` expuestas, `redis ping = True`, TCP a `tasker-db-pg:5432 = OK`, log muestra `event storage backend: redis`; Neo4j (7474) → 200, mock-api (`/mock/issues`, `/docs`) → 200, board (19001) → 200.
- **Fallback:** sin env → `("memory", MemoryStorage)`; Redis caído → `memory` (verificado en el contenedor y en unit tests).
- **Gates:** `ruff check src/` = 1011 (baseline), `mypy src/` = 1155/133 (≤ 1158/133), `pytest -q` = 1101 passed (+8 tests nuevos) / 27 skipped / 3 failed idénticos al baseline (verificados como preexistentes con los cambios stashados).

## Files to Create
- `src/socialseed_tasker/config/storage.py` — módulo de config compartido (web + CLI)
- `tests/config/test_storages_unit.py` — unit tests del patrón fallback

## Files to Modify
- `docker-compose.yml` — servicios `tasker-db-pg`, `tasker-redis`, env y `depends_on` de `tasker-api`
- `src/socialseed_tasker/cli/wiring.py` — consume `build_storage()`/`get_redis_url()` del módulo compartido
- `src/socialseed_tasker/infrastructure/web_api/app.py` — events/session store vía `build_storage()` con backend en `app.state.storage_backend`
- `pyproject.toml` — `redis>=5.0.0` en dependencias main (la imagen de la API lo necesita)
- `features.md` — §1 (infra) cuando esté done

## Related Issues
- #304 (Redis StoragePort adapter), #305 (Celery + Redis), #311 (Rate limiting), #519 (auth que consumirá estos servicios), #526/#527 (issues dependientes)
