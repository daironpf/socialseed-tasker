# Issue #533: Health con Redis/Postgres y tarjetas de sistema

## Description

`GET /health` solo reporta Neo4j (`dependencies.neo4j`) más la configuración de auth/rate-limiting, y `DashboardSystemView` muestra Neo4j (con latencia), API (versión) y Workers. Con la infraestructura de la ÉPICA 1 (#525), `notas.md` pide un indicador de salud en tiempo real que valide el estado de **Neo4j, Redis y Postgres**.

Origen: `notas.md` → ÉPICA 5 · Issue #11 (→ #533). Las tarjetas de métricas (Total Issues, Blocked, Components, Agents Working) y las acciones admin de seed/reset ya existen (#72, #67, §14): esta issue cubre el health multi-dependencia y su reflejo en la UI.

## Status: DONE (2026-10-01)

## Priority: MEDIUM

## Component
Backend + Frontend / Health / Dashboard

## Type
feat / infra

## Implementation
1. **`/health` ampliado:** ping a Redis (`PING`, `socket_connect_timeout=1`) cuando `TASKER_REDIS_URL` está definido y a Postgres (`SELECT 1` con `connect_timeout=1`) cuando `TASKER_DATABASE_URL` está definido → `dependencies: {neo4j, redis, postgres, httpx}` con `connected`/`disconnected`/`not configured`; `status: degraded` si algún servicio configurado está caído (mismo criterio que Neo4j); nuevo bloque `dependency_latency_ms` con la latencia medida de cada ping (incluye Neo4j).
2. **Alias `/api/v1/health`:** el cliente real usa base `/api/v1` y el endpoint vivía solo en la raíz (`GET /api/v1/health` → 404 en modo real); se registra el mismo handler en ambas rutas (alias oculto de OpenAPI) y se añade a las exenciones de auth/rate-limit (las health probes no requieren API key).
3. **`systemApi.fetchSystemHealth`:** adapta el payload plano real (`dependencies`/`dependency_latency_ms`/`version`) al shape de `SystemHealth` (`services.{neo4j,redis,postgres}.{status,latency_ms}`, `services.api.version`); el envelope mock se devuelve tal cual.
4. **DashboardSystemView:** tarjetas Redis (rose) y PostgreSQL (indigo) con estado + latencia junto a Neo4j; badge dinámico (connected/running → verde, disconnected → rojo, no configurado → gris) para Neo4j/Redis/Postgres; latencia oculta si no existe; el botón Refresh existente re-fetcha.
5. **mock parity:** `/mock/health` (mock-api) incluye `services.redis`/`services.postgres` para que el modo mock muestre las tarjetas.
6. **i18n** EN/ES: `system.redis`, `system.postgres`, `system.keyValueStore`, `system.relationalDb`, `system.notConfigured`; sin dependencias nuevas (`redis`/`psycopg[binary]` ya estaban en `pyproject.toml` desde #525–#527).

## Acceptance Criteria
- [x] `GET /health` reporta `dependencies.neo4j`, `dependencies.redis` y `dependencies.postgres` con su estado
- [x] `status: degraded` cuando un servicio configurado está caído; `not configured` cuando no hay URL/env
- [x] El System Dashboard muestra las tarjetas Redis/Postgres y las actualiza con Refresh
- [x] i18n support (EN + ES); `npm run build` passes
- [x] Gates backend sin regresiones

## Verification
- **Gates backend:** `ruff check src/` = **1011** (baseline) ✓ · `mypy src/` = **1151/133** (baseline) ✓ · `pytest -q` = **1184 passed / 27 skipped / 3 failed** (los mismos 3 preexistentes: `test_delivery_retries`, 2x `test_tasks_unit`; +6 tests nuevos) ✓
- **Tests nuevos:** `tests/api/test_health_dependencies.py` (6) — las 3 claves presentes con valores del conjunto permitido, `not configured` + `healthy` sin env, Redis inalcanzable → `disconnected` + `degraded` + latencia, Postgres inalcanzable → `disconnected` + `degraded`, alias `/api/v1/health` = payload de raíz, alias sin API key → 200 mientras `/api/v1/issues` → 401 ✓
- **Gates frontend:** `npm run lint` 0 errores (2 warnings preexistentes vue/no-mutating-props) · `npm test` = **208/208** · `npm run build` (vue-tsc) verde ✓
- **Smoke live (stack compose, api+board+mock-api reconstruidos):** `GET /api/v1/health` → 200 `status: healthy`, `dependencies = {neo4j: connected, redis: connected, postgres: connected, httpx: available}`, `dependency_latency_ms = {neo4j: 4.83, redis: 3.93, postgres: 14.76}` · `GET /health` raíz → 200 con el mismo payload · alias sin key → 200 (exento de auth) · `/mock/health` → `services.redis/postgres = (connected, 8/15 ms)` · bundle servido por el board contiene las claves nuevas (`keyValueStore`, `notConfigured`, `relationalDb`, ES incluido) ✓
- **Nota (fuera de alcance):** las tarjetas de métricas del dashboard (total_issues, blocked, etc.) siguen en 0 en modo real porque el backend no expone esas métricas en `/health` (el issue las excluye explícitamente como ya existentes en mock); preexistente, candidato a issue aparte.

## Files to Create
- `tests/api/test_health_dependencies.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` — pings Redis/Postgres + `dependency_latency_ms` + alias `/api/v1/health` + exenciones auth/rate-limit
- `frontend/src/api/systemApi.ts` — adapter de payload real plano → `SystemHealth`
- `frontend/src/types/index.ts` — `HealthDependencies`, `SystemHealth.dependencies`/`dependency_latency_ms`, `services.redis/postgres` opcionales
- `frontend/src/views/DashboardSystemView.vue` — tarjetas Redis/Postgres + badges dinámicos
- `frontend/src/locales/en.json` / `es.json` — `system.redis/postgres/keyValueStore/relationalDb/notConfigured`
- `mock-api/server.py` — `services.redis`/`services.postgres` en `/mock/health`
- `features.md` — §14

## Related Issues
- #66 (Neo4j status in health), #402 (Health endpoint tests), #407 (Stale Neo4j status), #72 (Project summary dashboard), #525 (servicios base)
