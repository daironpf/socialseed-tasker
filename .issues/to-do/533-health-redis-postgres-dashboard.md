# Issue #533: Health con Redis/Postgres y tarjetas de sistema

## Description

`GET /health` solo reporta Neo4j (`dependencies.neo4j`) más la configuración de auth/rate-limiting, y `DashboardSystemView` muestra Neo4j (con latencia), API (versión) y Workers. Con la infraestructura de la ÉPICA 1 (#525), `notas.md` pide un indicador de salud en tiempo real que valide el estado de **Neo4j, Redis y Postgres**.

Origen: `notas.md` → ÉPICA 5 · Issue #11 (→ #533). Las tarjetas de métricas (Total Issues, Blocked, Components, Agents Working) y las acciones admin de seed/reset ya existen (#72, #67, §14): esta issue cubre el health multi-dependencia y su reflejo en la UI.

## Status: TODO

## Priority: MEDIUM

## Component
Backend + Frontend / Health / Dashboard

## Type
feat / infra

## Implementation
1. **`/health` ampliado:** ping a Redis (`PING` → `PONG`) y a Postgres (`SELECT 1`) con timeout corto → `dependencies: {neo4j, redis, postgres}` con valores `connected`/`disconnected`/`not configured`; `status: degraded` si algún servicio configurado está caído (mismo criterio que el de Neo4j).
2. **DashboardSystemView:** tarjetas Redis y Postgres (estado + latencia) junto a Neo4j; reutilizar el botón Refresh existente para el refetch.
3. **i18n** de las nuevas tarjetas; sin dependencias nuevas si `redis`/`psycopg` llegaron con #525–#527.

## Acceptance Criteria
- [ ] `GET /health` reporta `dependencies.neo4j`, `dependencies.redis` y `dependencies.postgres` con su estado
- [ ] `status: degraded` cuando un servicio configurado está caído; `not configured` cuando no hay URL/env
- [ ] El System Dashboard muestra las tarjetas Redis/Postgres y las actualiza con Refresh
- [ ] i18n support (EN + ES); `npm run build` passes
- [ ] Gates backend sin regresiones

## Files to Create
- `tests/api/test_health_dependencies.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` — `health_check()` con pings Redis/Postgres
- `frontend/src/views/DashboardSystemView.vue` — tarjetas nuevas
- `frontend/src/api/systemApi.ts` — tipos de `dependencies.redis/postgres`
- `frontend/src/locales/en.json` / `es.json`
- `features.md` — §14

## Related Issues
- #66 (Neo4j status in health), #402 (Health endpoint tests), #407 (Stale Neo4j status), #72 (Project summary dashboard), #525 (servicios base)
