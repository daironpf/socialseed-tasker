# Issue #588: `DELETE /policies/{id}` devuelve 200 pero no borra nada (borra en una caché en memoria, la lista se lee de Neo4j)

## Description

Borrar una policy **miente**: responde `200 {"deleted": "<id>"}` pero la policy sigue
ahí. Verificado **dos veces** en el backend real:

1. Corrida run4 de la auditoría (2026-10-20): DELETE → 200, la policy seguía en el
   listado (confirmación con 2 lecturas).
2. Repro independiente (2026-10-21, `app.debug=True`, contenedor `tasker-api`):

```
POST /api/v1/policies {"name":"DBG-PROBE-policy", ...}  -> 201  (id 565c3bc4-...)
DELETE /api/v1/policies/565c3bc4-...                    -> 200  {"deleted":"565c3bc4-..."}
GET  /api/v1/policies?page=1&limit=50                   -> 200  lista la contiene
STILL PRESENT: True
```

**Causa raíz** en `src/socialseed_tasker/infrastructure/web_api/routers/policy.py:416-425`:

```python
def delete_policy(policy_id: str) -> APIResponse[dict]:
    policies = _policy_engine.get("policies", [])
    _policy_engine["policies"] = [p for p in policies if str(p.id) != policy_id]
    return APIResponse(data={"deleted": policy_id}, meta=Meta(request_id=None))
```

El handler filtra el dict **en memoria** `_policy_engine` (que además no estaba
poblado con la policy recién creada en Neo4j → ni siquiera eso cambia nada), mientras
`list_policies` (policy.py:345) y `get_policy` (policy.py:390) leen
`PolicyRepository` sobre **Neo4j**. El borrado nunca llega al grafo. Efecto lateral
de la auditoría: la policy sobreviviente hubo que eliminarla a mano con Cypher
(`MATCH (n:Policy) DETACH DELETE n`) — una "limpieza" no debería requerir shell de
Neo4j.

Además el endpoint ni siquiera valida existencia: borrado de un id inexistente → 200
igual.

## Status: DONE (commit pendiente)

## Priority: HIGH

## Component
Backend / Policies (router + repositorio Neo4j)

## Type
bug fix / backend

## Implementation

1. **Borrar en Neo4j** (`policy.py` `delete_policy`):
   - Delegar en `PolicyRepository` (`infrastructure/neo4j_policy_repository.py`): método
     `delete_policy(policy_id)` con `MATCH (p:Policy {id: $id}) DETACH DELETE p` (o
     `DETACH DELETE` + limpieza de índices RAG si la policy estaba indexada — revisar
     el alta: `create_policy` llama a `rag_repo.create_native_embedding(...)` en
     policy.py:316, así que el delete debería retirar ese embedding también).
   - Id inexistente → **404** (`Policy not found`), no 200 fantasma.
   - Sin driver/Neo4j → 503 (patrón del resto del router).
2. **`_policy_engine`**: decidir su destino (SRP): si es estado de validación/dry-run
   en memoria, que `delete_policy` no lo toque (o que se recargue de Neo4j); no puede
   ser el target de un DELETE cuyo listado lee otra fuente. Auditar quién más usa
   `_policy_engine` para no romper `validate`/`dry-run`.
3. **Tests** (hoy no existe ninguno que fije el borrado real):
   - `test_delete_policy_removes_from_neo4j`: crear → DELETE 200 → `GET /policies` ya
     no la lista → `GET /policies/{id}` → 404.
   - `test_delete_policy_unknown_id_404`.
   - `test_delete_policy_503_without_driver`.

## Acceptance Criteria
- [x] `DELETE /api/v1/policies/{id}` → 200 y la policy desaparece de
      `GET /policies` **y** del grafo (`cypher-shell`: `MATCH (p:Policy) RETURN count(*)`
      → 0 tras borrar la única)
- [x] Id inexistente → 404 (ya no 200)
- [x] El embedding RAG asociado (si el alta lo creó) queda limpio también
- [x] `validate`/`dry-run` siguen funcionando tras el cambio (el engine en memoria no
      se rompe)
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/policy.py` (líneas 416-425)
- `src/socialseed_tasker/infrastructure/neo4j_policy_repository.py` (método `delete_policy`)
- `tests/api/` — tests de borrado real

## Related Issues
- #585 (los listados/linkages de policies también tienen 500 por parámetros), #594
  (observabilidad), #593 (guard de 403 en otras superficies admin)

## Notes
- **Repro**: crear policy vía API → DELETE → GET lista → sigue presente. Tras arreglar,
  repetir este flujo como test.
- El patrón correcto ya existe en el mismo router: `create_policy` (línea 271) sí escribe
  en Neo4j con `PolicyRepository(driver)` — el delete debe hablar con el mismo repo.

### Resolución (2026-10-22)

**Fix** en `routers/policy.py`:

- `delete_policy`: ya no toca `_policy_engine` — ahora recibe `Request`, obtiene el
  driver de `app.state.driver` (503 si `None`, patrón del resto de routers),
  `PolicyRepository.get_policy` para validar existencia (id inexistente → **404**,
  ya no 200 fantasma), `PolicyRepository.delete_policy` (query ya existente
  `DELETE_POLICY` = `MATCH (p:Policy {id: $id}) DETACH DELETE p` en
  `neo4j_policy_repository.py:115`) y finalmente
  `RAGRepository.delete_by_source("policy", id)` para retirar embeddings RAG
  (el alta usa `create_native_embedding` que guarda `n.embedding` en el propio
  nodo — el `DETACH DELETE` lo elimina; `delete_by_source` cubre además
  `RAGEmbedding` separados si existieran).
- `get_policy`: descubrimiento durante la investigación — la issue afirmaba que leía
  Neo4j pero en realidad **también leía el dict muerto `_policy_engine`** (siempre
  vacío → `GET /policies/{id}` devolvía 404 para toda policy existente). Corregido
  para leer `PolicyRepository` (503/404/200 coherente con `list_policies`), de modo
  que el borrado sea observable vía `GET /policies/{id}` y no solo vía el listado.
  Helper `_policy_to_response` compartido con `list_policies` (refactor puro).
- `_policy_engine` queda intacto para `dry_run_policy` (policy.py) y
  `dependencies.py` (enforcement de `add_dependency`) — tests
  `tests/unit/test_max_depth_write_time.py` que lo pueblan siguen verdes.

**Tests** `tests/api/test_delete_policy_roundtrip.py` (4, fake driver emulando
`CREATE_POLICY`/`GET_POLICY`/`LIST_POLICIES`/`DELETE_POLICY`/`delete_by_source`):
roundtrip crear → GET by id 200 → DELETE 200 → nodo fuera del store → lista vacía →
GET by id 404; id inexistente → 404; limpieza de `RAGEmbedding` por `sourceType`;
503 sin driver.

**Verificación en vivo** (tasker-api reconstruido, 2026-10-22): 12/12 checks —
login, POST 201 (id `3c49f207-…`), GET by id 200, lista lo contiene, nodo en grafo,
DELETE 200 con `deleted` correcto, lista ya sin él, GET by id 404, DELETE
inexistente 404, nodos 5 → 5, 0 `Policy` y 0 `RAGEmbedding{sourceType:'policy'}`
en el grafo, `docker logs` sin ERROR/Traceback.

**Gates**: `ruff check policy.py` 11 (HEAD 14, delta −3; test fichero limpio),
`mypy src/` 1120 = baseline, `pytest -q` **1591 passed / 62 skipped / 0 failed**.
