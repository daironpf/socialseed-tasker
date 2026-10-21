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

## Status: OPEN

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
- [ ] `DELETE /api/v1/policies/{id}` → 200 y la policy desaparece de
      `GET /policies` **y** del grafo (`cypher-shell`: `MATCH (p:Policy) RETURN count(*)`
      → 0 tras borrar la única)
- [ ] Id inexistente → 404 (ya no 200)
- [ ] El embedding RAG asociado (si el alta lo creó) queda limpio también
- [ ] `validate`/`dry-run` siguen funcionando tras el cambio (el engine en memoria no
      se rompe)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

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
