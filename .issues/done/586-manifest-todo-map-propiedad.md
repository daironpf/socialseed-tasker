# Issue #586: `PATCH /issues/{id}/manifest/todo` → 500 — guarda una lista de maps como propiedad de nodo Neo4j

## Description

Actualizar el TODO del manifiesto de una issue falla con `500` cuando el body es el
contrato correcto (lista de objetos) y la issue existe:

```
PATCH /api/v1/issues/{issue_id}/manifest/todo
  body={"todo": [{"task": "t1", "completed": false}]}
-> 500
  neo4j.exceptions.CypherTypeError:
  Property values can only be of primitive types or arrays thereof.
  Encountered: Map{task -> String("t1"), completed -> String("False")}.
  {gql_status: 22N01 / 22G03}
```

(Reproducido in-process 2026-10-21 con `app.debug=True` sobre una **issue real**
creada para la prueba; en run4 el endpoint figuraba como ERR.)

Body con `{"todo": ["t1"]}` (strings) → `422` correcto
(`ManifestTodoRequest` exige `ManifestTodoItem{task, completed}` en
`schemas.py:215-229`) — el schema del contrato **no** es el problema.

**Causa raíz**: `routers/issues.py:1125`:

```python
todo_list = [{"task": item.task, "completed": str(item.completed)} for item in body.todo]
updated_issue = repo.update_manifest_todo(issue_id, todo_list)
```

Se construye una **lista de diccionarios** y `update_manifest_todo` la guarda como
valor de propiedad de un nodo — Neo4j solo admite primitivos (o arrays de primitivos)
como propiedades → `CypherTypeError` → 500. Dos defectos extra en la misma línea:

- `str(item.completed)` convierte el bool en `"False"`/`"True"` (string): aunque se
  serializara a JSON, el tipo sería incorrecto para un consumidor que espere bool.
- La serialización a string (necesaria para caber en una propiedad) simplemente no se
  hace: falta un `json.dumps(...)` en el guardar y un `json.loads(...)` al leer.

## Status: DONE

## Priority: MEDIUM

## Component
Backend / Neo4j (manifest de issues)

## Type
bug fix / backend

## Implementation

1. **Serializar al guardar** (`routers/issues.py:1125` y/o
   `neo4j_impl/issue_mixin.py::update_manifest_todo`):
   - `json.dumps([{"task": i.task, "completed": i.completed} for i in body.todo])` →
     string plano (propiedad válida) **o** array de strings si el patrón del repo
     prefiere eso.
   - `completed` como **bool** dentro del JSON (adiós a `str(False)` → `"False"`).
2. **Leer de forma simétrica**: localizar dónde se lee el manifest (`GET /issues`,
   `GET /issues/{id}`, `IssueResponse`) y parsear con `json.loads` (+ tolerar el
   formato legado si había algo escrito antes — con el bug siempre fue 500, así que lo
   más probable es que no existan nodos con manifest; verificar igualmente).
3. **Tipado del contrato**: `ManifestTodoItem.completed: bool` ya está bien en
   `schemas.py` — no tocar el contrato público; arreglar solo la persistencia.
4. **Tests**:
   - `test_patch_manifest_todo_roundtrip`: PATCH con 2 items → 200 → GET devuelve los
     mismos items con `completed` bool.
   - `test_patch_manifest_todo_with_completed_true` (bool `true`, no string).
   - Test con issue inexistente → 404 (comportamiento actual correcto: ya se vió 404).

## Acceptance Criteria
- [x] `PATCH /issues/{id}/manifest/todo` con `{"todo":[{"task","completed"}]}` e issue
      real → 2xx (ya no `CypherTypeError`/500)
- [x] Roundtrip: el `GET` de la issue devuelve los items con `completed` como bool
- [x] La propiedad almacenada es primitiva (string JSON o array de strings), nunca un
      map
- [x] Issue inexistente → 404 (sin cambios)
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/issues.py` (línea 1125)
- `src/socialseed_tasker/infrastructure/neo4j_impl/issue_mixin.py`
  (`update_manifest_todo`)
- `tests/api/` — roundtrip de manifest

## Related Issues
- #585 (misma familia de "lo que se manda no es lo que la query espera"), #578/#584
  (otros 500 de escritura), #594 (observabilidad), #595 (OpenAPI)

## Notes
- **Repro**: crear issue → `curl -X PATCH .../api/v1/issues/{id}/manifest/todo -d
  '{"todo":[{"task":"t1","completed":false}]}'` → 500 con `CypherTypeError` en el
  detalle de debug.
- Los hermanos `manifest/files` y `manifest/notes` (issues.py:1130, 1154) guardan
  `list[str]`/`str` — comprobar al implementar que no repiten el bug de los maps
  (`files` es array de strings: primitivo permitido, debería estar bien).
- **Fix (2026-10-22):**
  - `routers/issues.py`: `completed` se pasa como **bool** real (adiós a
    `str(False)` → `"False"`).
  - `neo4j_impl/issue_mixin.py::update_manifest_todo`: serializa con
    `json.dumps(todo)` → propiedad string primitiva; `create_issue` hace lo mismo si
    `manifest_todo` no está vacío (antes pasaba la lista cruda también al crear).
  - Lectura simétrica: helper `_parse_manifest_todo` en `neo4j_impl/shared.py`
    (`json.loads` tolerante, admite lista legada y filtra no-dicts) usado por
    `_node_to_issue` y `get_manifest`.
  - Tipos: `manifest_todo` / `ManifestResponse.todo` → `list[dict[str, Any]]`
    (domain `entities`, `schemas`, firmas en `actions`/`api_repository`/`issue_mixin`)
    — el contrato request (`ManifestTodoItem.completed: bool`) no se tocó.
- **Tests:** `tests/api/test_manifest_todo_roundtrip.py` (4): roundtrip PATCH→GET
  con bools + assert de propiedad primitiva (`isinstance(str)` + `json.loads`),
  `completed True` como bool, issue inexistente → 404, variantes del parser.
- **Gates:** ruff src **1002** (=), fichero de tests nuevo limpio (los 247 de
  `ruff check tests` son preexistentes — idénticos con el fichero excluido),
  mypy **1120** (=, verificado contra HEAD vía `git stash`), pytest
  **1587 passed / 62 skipped / 0 failed**.
- **Verificación en vivo** (rebuild + force-recreate, 2026-10-22): **0 fallos** —
  PATCH → 200 con roundtrip bool en PATCH/GET issue/GET manifest, propiedad
  `i.manifestTodo` **str** en Neo4j (primitiva), PATCH inexistente → 404, DELETE de
  limpieza, nodos 5→5, `docker logs tasker-api` sin ERROR/Traceback/CypherTypeError.
- **Hermandad confirmada:** `manifest/files` y `manifest/notes` guardan arrays de
  strings (primitivos) — no repiten el bug; sin cambios.
