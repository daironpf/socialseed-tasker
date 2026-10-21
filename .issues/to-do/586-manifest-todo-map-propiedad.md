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

## Status: OPEN

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
- [ ] `PATCH /issues/{id}/manifest/todo` con `{"todo":[{"task","completed"}]}` e issue
      real → 2xx (ya no `CypherTypeError`/500)
- [ ] Roundtrip: el `GET` de la issue devuelve los items con `completed` como bool
- [ ] La propiedad almacenada es primitiva (string JSON o array de strings), nunca un
      map
- [ ] Issue inexistente → 404 (sin cambios)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

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
