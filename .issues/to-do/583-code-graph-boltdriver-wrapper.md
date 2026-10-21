# Issue #583: Code graph → 500 (`'BoltDriver' object has no attribute 'driver'`) — `CodeGraphRepository` recibe el driver crudo

## Description

Con el driver real conectado, el resto de endpoints de code graph (los que sí
declaran `Depends(get_code_graph_driver)`) revientan dentro de la sesión:

```
GET /api/v1/code-graph/stats -> 500
  routers/code_graph.py:221 code_graph_stats
  neo4j_code_graph_repository.py:419 get_stats
  neo4j_impl/shared.py:22 _session
AttributeError: 'BoltDriver' object has no attribute 'driver'
```

(Reproducido in-process 2026-10-21 con `app.debug=True`; en run4 los 11 endpoints
`code-graph/*` salieron ERR.)

**Causa raíz**: `src/socialseed_tasker/infrastructure/neo4j_impl/shared.py:21-22`:

```python
def _session(driver: Any) -> Iterator[Any]:
    with driver.driver.session(database=driver.database) as session:
```

`_session` asume un **wrapper** con atributos `.driver` y `.database`, pero
`CodeGraphRepository` construido desde el router recibe el objeto devuelto por
`retrieve_neo4j_code_graph_driver`, que en el stack real es un `BoltDriver` crudo →
`driver.driver` no existe → 500.

Detalle contradictorio: en dev sin Neo4j estos endpoints responden 200 con
`{"error": "Neo4j not connected"}` (guard `if not driver`), y en el proceso local
`GET /code-graph/stats` devolvió 200 — el bug **solo se manifiesta con driver real**,
que es exactamente el modo productivo.

Ya existe precedente de normalización en el repo: `routers/project.py:533-534` hace
`driver.driver if hasattr(driver, "driver") else driver` y
`driver.database if hasattr(...) else "neo4j"`.

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / Code graph (`CodeGraphRepository` + `neo4j_impl/shared`)

## Type
bug fix / backend

## Implementation

1. **Normalizar en un solo punto** — elegir uno:
   - Opción A (recomendada): `_session` de `neo4j_impl/shared.py` acepta ambos shapes
     con `hasattr` (patrón ya usado en `project.py:533-534`), o
   - Opción B: `CodeGraphRepository.__init__` (`neo4j_code_graph_repository.py`)
     normaliza antes de repartir `self._driver`.
   Ojo con el alcance: `_session` es compartido por los mixins de Neo4j
   (`epic_mixin`, `issue_mixin`, etc.) — si algún call-site pasa wrapper y otros
   driver crudo, la normalización debe servir a ambos sin romper los que ya funcionan.
2. **Determinar qué recibe cada cual**: auditar `get_code_graph_driver` (importado en
   `code_graph.py:109` como `retrieve_neo4j_code_graph_driver`) vs `app.state.driver`
   (wrapper usado por `PolicyRepository` y cía.) — si salen shapes distintos,
   unificar a uno solo (SRP: una forma de driver por proceso).
3. **Tests**:
   - Test de `_session`/`get_stats` con **driver crudo simulado** (objeto con
     `.session(database=...)` pero sin `.driver`) → no AttributeError.
   - Test con wrapper (`.driver` + `.database`) → sin regresión.
   - `test_code_graph_stats_200_with_real_shape`.

## Acceptance Criteria
- [ ] `GET /code-graph/stats` (y el resto: `files`, `symbols`, `calls/{name}`,
      `depends/{path}`, `tests/{path}`, `issues/{path}`, `symbols/{id}`,
      `callers`, `callees`, `POST analyze/impact`) → 200 con el driver real, ya no
      `AttributeError`/500
- [ ] `_session` (o su call-site) soporta driver crudo **y** wrapper sin regresión en
      los repos que hoy funcionan (epics, issues, policies…)
- [ ] Un solo criterio de "forma del driver" en el proceso (documentado en el código)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/neo4j_impl/shared.py` (líneas 21-22) y/o
- `src/socialseed_tasker/infrastructure/neo4j_code_graph_repository.py` (constructor /
  `get_stats` línea 419)
- `src/socialseed_tasker/infrastructure/web_api/routers/code_graph.py` (si se unifica
  la dependencia)
- `tests/` — tests de ambos shapes

## Related Issues
- #582 (los otros dos endpoints de code-graph tienen bug propio: NameError), #594
  (observabilidad), #595 (OpenAPI)

## Notes
- **Repro**: `curl 'http://127.0.0.1:8888/api/v1/code-graph/stats' -H 'X-API-Key:
  test-token'` → 500. En proceso sin Neo4j → 200 con guard: el test debe cubrir la
  rama con driver.
- Verificado in-process 2026-10-21 dentro de `tasker-api` (imagen `7cbfc5b`).
