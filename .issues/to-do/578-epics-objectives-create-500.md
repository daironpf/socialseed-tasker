# Issue #578: `POST /epics` y `POST /objectives` devuelven 500 — atributo `createdAt` inexistente en el modelo

## Description

Alta de epics y objectives **rota por completo** contra el backend real: cualquier
`POST /api/v1/epics` o `POST /api/v1/objectives` con body válido devuelve
`500 INTERNAL_ERROR` y no crea nada (`GET /epics` y `GET /objectives` siguen en `[]`).

Reproducido en vivo el 2026-10-21 contra `tasker-api` (imagen reconstruida a `7cbfc5b`),
con `app.debug=True` + TestClient dentro del contenedor (`docker exec tasker-api`):

```
POST /api/v1/epics {"name": "DBG epic", "description": "dbg"} -> 500
  routers/epic.py:146 create_epic
  neo4j_impl/epic_mixin.py:23 create_epic
AttributeError: 'Epic' object has no attribute 'createdAt'. Did you mean: 'created_at'?

POST /api/v1/objectives {...} -> 500
  routers/objective.py:146 create_objective
  neo4j_impl/epic_mixin.py:90 create_objective
AttributeError: 'Objective' object has no attribute 'createdAt'. Did you mean: 'created_at'?
```

**Causa raíz**: `EpicRepositoryMixin.create_epic`/`create_objective` escriben
`epic.createdAt.isoformat()` / `objective.createdAt.isoformat()`
(`neo4j_impl/epic_mixin.py:23-24` y `90-91`) pero las entidades Pydantic de dominio
exponen `created_at`/`updated_at` en snake_case (el propio Pydantic sugiere
`created_at`). El mismo camelCase asumido sí existe en el **alambrado wire** de la API,
no en el modelo de dominio — de ahí el choque. Los GET funcionan porque leen con
`node.get(...)` sin pasar por atributos camelCase.

Mismo patrón que `POST /commits` (#584) y que la familia de parámetros Cypher (#585).

## Status: OPEN

## Priority: HIGH

## Component
Backend / Neo4j (repositorio de epics y objectives)

## Type
bug fix / backend

## Implementation

1. **Fix de mapeo** (`src/socialseed_tasker/infrastructure/neo4j_impl/epic_mixin.py`):
   - Línea 23-24 (`create_epic`): usar los campos reales del modelo
     (`epic.created_at` / `epic.updated_at` — verificar nombres exactos en
     `domain/entities.py`; Pydantic ya nos da la pista) con
     `isoformat()`/`str(...)` igual que hoy.
   - Línea 90-91 (`create_objective`): ídem.
   - Revisar si `Epic`/`Objective` llegan al mixin con `created_at` poblado desde el
     router (`routers/epic.py:133+`, `routers/objective.py:133+`): si el router no lo
     pasa, el mixin debe usar `datetime.now(timezone.utc)` como fallback (los nodos
     siempre deben tener fecha de creación).
   - Auditar en el mismo mixin el resto de accesos camelCase (`updatedAt`, etc.) para
     no dejar un segundo 500 latente en la misma ruta.
2. **Guardia anti-regresión**: si el modelo cambia de nombre otra vez, que falle el
   test, no el endpoint en producción.
3. **Tests** (nuevos en `tests/api/`, patrón de los CRUD existentes):
   - `test_create_epic_roundtrip`: POST 201/200 → GET /epics lo lista → GET
     `/epics/{id}` lo devuelve con fechas coherentes.
   - `test_create_objective_roundtrip`: ídem con objectives.
   - Test sobre el mixin con driver fake que fija que `session.run` recibe
     `createdAt`/`updatedAt` como strings ISO (contrato de la query CREATE_EPIC).

## Acceptance Criteria
- [ ] `POST /api/v1/epics` con `{"name": ...}` → 2xx (ya no 500) y el epic aparece en
      `GET /epics` y `GET /epics/{id}`
- [ ] `POST /api/v1/objectives` con `{"name": ...}` → 2xx y aparece en `GET /objectives`
- [ ] Los nodos creados tienen `createdAt`/`updatedAt` en Neo4j (la query
      `CREATE_EPIC`/`CREATE_OBJECTIVE` recibe strings ISO)
- [ ] Sin accesos `camelCase` a atributos Pydantic en `epic_mixin.py`
- [ ] Gates: `ruff check src/` sin delta, `mypy src/` sin delta, `pytest -q` sin nuevas
      fallas (los tests nuevos pasan)

## Files to Modify
- `src/socialseed_tasker/infrastructure/neo4j_impl/epic_mixin.py` (líneas 23-24, 90-91)
- `src/socialseed_tasker/infrastructure/web_api/routers/epic.py` / `objective.py` (si el
  router no puebla `created_at`)
- `tests/api/` — test nuevo de roundtrip de creación

## Related Issues
- #584 (mismo patrón camelCase en `POST /commits`), #585 (familia de parámetros
  Cypher mal enlazados), #579 (PATCH de epics/objectives con body vacío → 500), #594
  (los 500 no dejaban traceback en logs)

## Notes
- **Repro**: `curl -X POST http://127.0.0.1:8888/api/v1/epics -H 'X-API-Key:
  test-token' -H 'Content-Type: application/json' -d '{"name":"t"}'` → hoy 500;
  tras el fix → 2xx.
- Tras crear epics/objectives en pruebas, limpiarlos (DELETE /epics, DELETE /objectives
  o Cypher) — el entorno real se dejó limpio tras la auditoría (#588 explica por qué
  borrar policies a mano).
