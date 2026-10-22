# Auditoría del backend real (294 endpoints) — Issue Index

**Fuente:** campaña de pruebas del API desplegado (`tasker-api` en `127.0.0.1:8888`,
imagen reconstruida a `7cbfc5b`), 2026-10-20/21.
**Created:** 2026-10-21
**Status:** OPEN (13/20 implementadas — issues **#578–#597** en `.issues/to-do/`)

> **Continuidad:** siguiente número libre tras **#577** (máximo en `.issues/done/`,
> cerrado el 2026-10-12), por lo que esta auditoría numeró **#578–#597**.

---

## Contexto y metodología

- **Stack probado en vivo:** `tasker-api` (8888), `tasker-board` (19001), `tasker-db`
  (neo4j 5.26 community), `tasker-db-pg`, `tasker-db-mongo`, `tasker-redis`.
  Auth real (`TASKER_AUTH_ENABLED=true`, `X-API-Key`/Bearer + JWT vía
  `POST /api/v1/auth/login`), rate limit 60/min por IP.
- **Corrida run4** (`results4.json`, 294 rutas): **PASS 154, GRACE 64, 4XX 30, ERR 38,
  SKIP 7, TIMEOUT 1** (0×422 inesperados tras corregir seeds).
- **Triaje de causas raíz:** los 38 ERR no se aceptaron "por status": se reprodujeron
  **in-process dentro del contenedor** con `app.debug = True` + `TestClient`
  (`docker cp` + `docker exec tasker-api python /tmp/debug*.py`) para capturar los
  tracebacks reales (el `generic_error_handler` no los loguea — ver **#594**).
  Confirmaciones por código (`grep` de queries/callers) para los heredados del run4.
- **Limpieza:** el entorno se dejó limpio (Neo4j: solo `User×2, Agent×2, Project×1`;
  policies/issues/components vacíos; PG/Mongo barridos). La policy de la prueba de
  #588 hubo que borrarla **a mano con Cypher** — el bug exactamente.

## Issue Index

| # | Issue | Priority | Type | Status |
|---|---|---|---|---|
| #578 | `POST /epics` y `/objectives` → 500 (`createdAt` inexistente en el modelo) | HIGH | bug fix / backend | DONE  |
| #579 | `PATCH /epics`/`/objectives` con body sin campos → 500 (Cypher `SET` vacío) | MEDIUM | bug fix / backend | DONE  |
| #580 | Los 4 `cost-*` → 500 (Cypher inválido: `WHEN 'JUNIOR'`, `hours` sin definir) | MEDIUM | bug fix / backend | DONE  |
| #581 | `GET /secrets/audit` → 500 (ruta sombreada por `/secrets/{name}`) | MEDIUM | bug fix / backend | DONE  |
| #582 | `GET /code-graph/files`/`symbols` → 500 (`NameError: driver`) | MEDIUM | bug fix / backend | DONE  |
| #583 | Code graph → 500 (`'BoltDriver' has no attribute 'driver'`) | MEDIUM | bug fix / backend | DONE  |
| #584 | `POST /commits` → 500 (`authorName` inexistente en el modelo) | MEDIUM | bug fix / backend | DONE  |
| #585 | 10 endpoints → 500 por parámetros Cypher mal enlazados (`$projectId` vs `project_id=`…) | HIGH | bug fix / backend | DONE  |
| #586 | `PATCH /issues/{id}/manifest/todo` → 500 (lista de maps como propiedad Neo4j) | MEDIUM | bug fix / backend | DONE  |
| #587 | `GET /projects/all` y `/current` → 400 (`ProjectResponse.slug=None` + fechas) | MEDIUM | bug fix / backend | DONE  |
| #588 | `DELETE /policies/{id}` → 200 pero no borra (borra en caché en memoria) | HIGH | bug fix / backend | DONE  |
| #589 | `POST /labels/sync` → 500 `Illegal header value b'token '` sin `GITHUB_TOKEN` | MEDIUM | bug fix / backend | DONE  |
| #590 | `POST /ai/.../embed` → 500 con `{"detail":"400: OPENAI_API_KEY not configured"}` | MEDIUM | bug fix / backend | OPEN |
| #591 | `GET /ai/similar-issues/{id}` → 500 (`Unknown function 'apoc.algo.similarity'`) | MEDIUM | bug fix / backend + infra | OPEN |
| #592 | Notificaciones con id no-ObjectId → 503 "store unavailable" en vez de 404 | MEDIUM | bug fix / backend | OPEN |
| #593 | 403 permanente en `/admin/tenants` y `POST /data-quality/rules` (RBAC solo por env `TASKER_AUTH_USERS`) | MEDIUM | bug fix / config | OPEN |
| #594 | Los 500 no dejan traceback en `docker logs` (handler sin `logger.exception`) | HIGH | bug fix / backend | DONE  |
| #595 | OpenAPI sin `requestBody` documentado + `affects` con cuerpo string crudo | MEDIUM | bug fix / docs-backend | OPEN |
| #596 | Faltan `DELETE`: `skills`, `mcp/servers`, `chat/conversations` | MEDIUM | feat / backend | OPEN |
| #597 | `GET /auth/login` (sin `/api/v1`) → TIMEOUT contra proxy OAuth `:4180` | LOW | bug fix / config | OPEN |

## Orden sugerido (dependencias)

1. **#594** primero — sin trazas en logs, cada fix posterior cuesta una repro manual.
2. **#578 → #584 → #579** (familia camelCase/escritura de entidades) y **#585** (fan-out
   de parámetros: toca muchos routers — hacerlo con su test de emparejamiento
   query↔caller).
3. **#582 + #583** (code graph: dos bugs distintos, mismo router), **#586**, **#587**,
   **#588** (borrado real de policies).
4. **#589, #590, #591** en bloque (mismo patrón: "config/falta de tercero no es 500").
5. **#592, #593** (códigos de estado engañosos), **#581** (orden de rutas).
6. **#595** (OpenAPI) antes o junto a rehacer el smoke; **#596** (DELETEs) independiente;
   **#597** (baja prioridad).

## Descartados (artefactos, NO bugs)

- `POST /agent-profiles` → 409: duplicado del seed (comportamiento esperado).
- `POST /agents/{id}/runs` → 404 con id `None`: el smoke no obtuvo el id (artefacto del
  script, no del server).
- `POST /epics`/`/objectives` → 400 en run4: el body auto-generado llevaba `name: ""`
  (minLength del schema) — **el 500 real** se confirmó después con body válido → #578.
- `POST /notifications/clear-all` → 503 `Event loop is closed`: artefacto del TestClient
  (en uvicorn real → **200** verificado 2026-10-21).
- `PATCH /epics/{id}` con campos → 200 (solo `{}` truena → #579).
- GETs de `data-quality` (`/rules`, `/reports`, `/metrics`) → 200 (solo escrituras dan
  403 → #593).
- Gaps de config sin issue propia (decisión de despliegue, no de código): ausencia de
  `OPENAI_API_KEY`/`GITHUB_TOKEN` en compose (el **comportamiento** ante su ausencia sí
  está cubierto en #589/#590).

## Related Done Issues

| Done | Relevante para |
|---|---|
| #547/#548 (notificaciones Mongo/REST) | #592 |
| #558/#564/#572/#576/#577 (esquema PG, CRUD, skills, agent-skills) | #596 |
| #527 (JWT con role/permissions) | #593 |
| #537/#551 (chat Mongo + store) | #596 |
| #517/#530 (SSE/realtime) | — |
| #555 (`tasker setup --build` siempre) | contexto de despliegue de esta auditoría |

---

## Release Checklist (backlog de auditoría)

- [ ] 20 issues implementadas — mover cada fichero a `.issues/done/` con `Status: DONE`
- [ ] Cada issue: gates backend (`ruff`/`mypy`/`pytest`); frontend (`lint`/`test`/`build`
      + i18n EN/ES) donde toque UI (#596)
- [ ] Re-correr el smoke completo (294 rutas) tras #578-#595 y actualizar el recuento
      (objetivo: 0 ERR de esta lista)
- [ ] Verificación en vivo sobre `tasker-api` desplegado (rebuild de imagen, patrón de
      #555) antes de dar por cerrada cada issue
- [ ] Commit solo tras `si` explícito; mensaje en español sin tildes referenciando
      `#NNN`
