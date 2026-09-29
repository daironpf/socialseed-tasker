# Issue #525: Docker Compose Hybrid Environment (PostgreSQL 15 + Redis 7)

## Description

`docker-compose.yml` solo orquesta Neo4j (`tasker-db`), la API (`tasker-api`), el board (`tasker-board`) y el mock (`mock-api`). La ÉPICA 1 de `notas.md` requiere una infraestructura multi-capa para autenticación y persistencia: PostgreSQL como store de usuarios/credenciales y Redis como store de sesiones y caché, relacionados con la API de FastAPI y la UI de Vue 3.

Origen: `notas.md` → ÉPICA 1 · Issue #1 (→ #525).

## Status: TODO

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
- [ ] `tasker-db-pg` (PostgreSQL 15) y `tasker-redis` (Redis 7 Alpine) definidos en `docker-compose.yml` con healthchecks
- [ ] `DATABASE_URL`, `REDIS_URL` y `JWT_SECRET` (convención `TASKER_*`) conectan la API con la DB y Redis
- [ ] Todos los contenedores arrancan con `docker compose up -d` y pasan sus healthchecks
- [ ] La API degrada con fallback in-memory/in-process cuando Redis/Postgres no están configurados
- [ ] Gates backend en baseline (`ruff`/`mypy`/`pytest`) sin regresiones

## Files to Create
- (ninguno)

## Files to Modify
- `docker-compose.yml` — servicios `tasker-db-pg`, `tasker-redis`, env y `depends_on` de `tasker-api`
- `src/socialseed_tasker/cli/wiring.py` (o módulo de config compartido) — lectura de `TASKER_DATABASE_URL`/`TASKER_REDIS_URL` accesible desde la capa web
- `features.md` — §1 (infra) cuando esté done

## Related Issues
- #304 (Redis StoragePort adapter), #305 (Celery + Redis), #311 (Rate limiting), #519 (auth que consumirá estos servicios), #526/#527 (issues dependientes)
