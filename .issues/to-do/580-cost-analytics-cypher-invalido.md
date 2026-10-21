# Issue #580: Los 4 endpoints de costos (`cost-*`) devuelven 500 — Cypher inválido en `neo4j_queries.py`

## Description

Todo el módulo de costos está caído contra el backend real: los 4 endpoints fallan con
`500 INTERNAL_ERROR` porque las queries Cypher tienen errores de sintaxis/tipos:

```
GET /api/v1/cost-summary         -> 500
  neo4j.exceptions.CypherSyntaxError:
  Type mismatch: expected Boolean but was String (line 5, column 22 (offset: 181))

GET /api/v1/cost-per-component   -> 500
  neo4j.exceptions.CypherSyntaxError:
  Variable `hours` not defined (line 7, column 36 (offset: 339))
  {gql_status: 50N42}
```

(También `GET /cost-per-epic` y `GET /cost-per-project` — misma familia, corrida run4
de la auditoría: los 4 dieron ERR.)

**Causa raíz**: `src/socialseed_tasker/infrastructure/neo4j_queries.py` líneas
**690, 695, 711, 727 y 741** construyen la tarifa por hora con:

```cypher
SUM(CASE WHEN 'JUNIOR' THEN hours * 75.0 ... END)
```

Dos errores en la misma cláusula:

1. `CASE WHEN 'JUNIOR' THEN ...` compara un **string literal** donde Neo4j espera un
   Boolean → `22NB1 Type mismatch: expected Boolean but was String`.
2. `hours` no está definido en el alcance de la consulta (`Variable 'hours' not
   defined`) — falta el `MATCH` de la relación/tier que aporte esas horas (o el nombre
   del campo real es otro).

Los valores de referencia sí existen: `domain/value_objects.py:24-31`
(`HourlyRateTier.JUNIOR: 75.0`), o sea que la query debía leer el tier del agente y
multiplicar `hours * rate[tier]`.

Los routers consumidores viven en `infrastructure/web_api/routers/cost_analytics.py`
(`/cost-per-component` en la línea 127 y compañía).

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / Neo4j (queries de analítica de costos)

## Type
bug fix / backend

## Implementation

1. **Reescribir las 5 consultas** en `neo4j_queries.py` (690-741):
   - `CASE WHEN <expresión booleana> THEN ...` — p.ej. `WHEN tier = 'JUNIOR'` sobre la
     propiedad real del nodo/relación (hallar de dónde sale el tier: nodo Agent,
     relación de asignación, etc. — inspeccionar el modelo del grafo con
     `cypher-shell` contra `tasker-db`).
   - Asegurar que `hours` viene de un `MATCH` (p.ej.
     `(i:Issue)-[:ASSIGNED_TO|WORKED_ON]->(a:Agent)` con la propiedad de horas) o
     renombrar al campo que realmente existe.
   - Unificar las 5 variantes (component/epic/project/summary) para que compartan la
     misma cláusula de tarifa (SRP: una sola fuente de verdad del cálculo).
2. **Validación en vivo**: ejecutar cada query directamente con `cypher-shell`
   (`docker exec tasker-db cypher-shell -u neo4j -p neoSocial "..."`) antes de darla
   por buena — con el grafo vacío deben devolver fila/`[]`, no error de sintaxis.
3. **Tests**: test de los endpoints que con driver fake o con la query construida
   fije que no contiene `WHEN 'JUNIOR'` literal ni `hours` huérfano (un test de
   "las queries compilan en Neo4j" con driver real de test, o fixtures de records).

## Acceptance Criteria
- [ ] `GET /cost-summary`, `/cost-per-component`, `/cost-per-epic`, `/cost-per-project`
      → 200 (con el grafo vacío: totales en 0 / listas vacías), ya no 500
- [ ] Las 5 sentencias de `neo4j_queries.py` (690-741) ejecutan sin
      `CypherSyntaxError`/`CypherTypeError` en el Neo4j real (`cypher-shell`)
- [ ] El cálculo usa `HourlyRateTier` de `domain/value_objects.py` como fuente de
      verdad de tarifas (sin números mágicos duplicados si es viable)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/neo4j_queries.py` (líneas 690-741)
- `src/socialseed_tasker/infrastructure/web_api/routers/cost_analytics.py` (solo si el
  mapeo de parámetros también está mal)
- `tests/` — cobertura de los 4 endpoints

## Related Issues
- #585 (familia de parámetros Cypher mal enlazados), #578/#584 (otros 500 de
  escritura), #594 (observabilidad), #595 (OpenAPI de estos endpoints)

## Notes
- **Repro**: `curl http://127.0.0.1:8888/api/v1/cost-summary -H 'X-API-Key:
  test-token'` → 500 con `CypherSyntaxError` en el detalle (vía debug) y envelope
  `INTERNAL_ERROR` en producción.
- Verificado in-process el 2026-10-21 con `app.debug=True` dentro de `tasker-api`.
