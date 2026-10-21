# Issue #582: `GET /code-graph/files` y `/symbols` → 500 (`NameError: name 'driver' is not defined`)

## Description

Dos endpoints del code graph fallan siempre con `500` cuando Neo4j está conectado:

```
GET /api/v1/code-graph/files   -> 500
  routers/code_graph.py:170 code_graph_files
NameError: name 'driver' is not defined

GET /api/v1/code-graph/symbols -> 500
  routers/code_graph.py:193 code_graph_symbols   (mismo patrón)
NameError: name 'driver' is not defined
```

(Tracebacks reproducidos in-process el 2026-10-21 con `app.debug=True` dentro de
`tasker-api`; en la corrida run4 de la auditoría ambos salían como ERR.)

**Causa raíz**: en `src/socialseed_tasker/infrastructure/web_api/routers/code_graph.py`
**los dos únicos handlers que no declaran la dependencia del driver**:

- `code_graph_files` (líneas 164-181): firma `async def code_graph_files(limit, language)`
  y usa `driver` en la línea 170 sin recibirlo.
- `code_graph_symbols` (líneas 184-209): ídem en la línea 193.

Todos los demás handlers del router sí lo reciben con
`driver: Any = Depends(get_code_graph_driver)` (p.ej. `code_graph_stats` línea 213,
`code_graph_clear` 231, `analyze/impact` 380…), por eso esos funcionan y estos dos no.
Como Python resuelve `driver` en tiempo de ejecución, el fallo solo salta con el
endpoint invocado (y en dev sin driver habría dado el mismo NameError, no el guard
`if not driver` que el autor pretendía).

## Status: DONE

## Priority: MEDIUM

## Component
Backend / Code graph (router)

## Type
bug fix / backend

## Implementation

1. **Añadir la dependencia** a los dos handlers (`code_graph.py:164-181` y `184-209`):
   ```python
   async def code_graph_files(
       limit: int = Query(50, ge=1, le=500),
       language: str | None = Query(None),
       driver: Any = Depends(get_code_graph_driver),
   ) -> dict[str, Any]:
   ```
   Conservando el guard `if not driver: return {"error": "Neo4j not connected"}`.
2. **Auditoría rápida del fichero**: comprobar que ningún otro handler del router usa
   `driver` sin declararlo (grep de `driver` vs firmas con `Depends`).
3. **Tests**:
   - `test_code_graph_files_returns_200_with_driver` (y con driver → estructura
     `{"files": [...], "total": n}`).
   - `test_code_graph_symbols_returns_200_with_driver`.
   - Test del guard sin driver → `{"error": "Neo4j not connected"}` sin NameError.

## Acceptance Criteria
- [ ] `GET /api/v1/code-graph/files` → 200 (lista o guard de "not connected"), ya no
      `NameError`/500
- [ ] `GET /api/v1/code-graph/symbols` → 200/422 según params, ya no 500
- [ ] Los dos handlers reciben el driver con el mismo `Depends` que el resto del
      router
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/code_graph.py` (líneas 164-181,
  184-209)
- `tests/api/` — tests de files/symbols

## Related Issues
- #583 (el resto de code-graph sí recibe driver pero truena con el wrapper — dos bugs
  distintos en el mismo router), #594 (observabilidad)

## Notes
- **Repro**: `curl 'http://127.0.0.1:8888/api/v1/code-graph/files' -H 'X-API-Key:
  test-token'` → 500 `INTERNAL_ERROR`.
- Tras el fix, `GET /code-graph/stats` debe seguir probándose aparte: tiene su propio
  bug (#583), no compartir causa con este.
