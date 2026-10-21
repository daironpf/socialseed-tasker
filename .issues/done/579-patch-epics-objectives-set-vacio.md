# Issue #579: `PATCH /epics/{id}` y `PATCH /objectives/{id}` con body sin campos de update → 500 (Cypher `SET` vacío)

## Description

El PATCH de epics/objectives **solo funciona si el body trae campos**; si llega `{}` o
cualquier body sin campos de actualización, la query Cypher se construye mal y Neo4j
rechaza la sentencia → `500`.

Reproducido en vivo 2026-10-21 (`app.debug=True`, TestClient en el contenedor):

```
PATCH /api/v1/epics/ph-epic  body={}    -> 500
  neo4j.exceptions.CypherSyntaxError:
  Invalid input 'e': expected an expression, '+=', '.', ':', '=', 'IS' or '['
  (line 1, column 38 (offset: 37))

PATCH /api/v1/epics/ph-epic  body={"name":"dbg","description":"dbg"} -> 200
PATCH /api/v1/objectives/ph-obj body={"name":"dbg","description":"dbg"} -> 200
```

**Causa raíz** en `neo4j_impl/epic_mixin.py:69-79` (`update_epic`):

```python
set_clauses = []
for key, value in updates.items():
    set_clauses.append(f"e.{key} = ${key}")
    params[key] = value
query = f"MATCH (e:Epic {{id: $id}}) SET {', '.join(set_clauses)} RETURN e"
```

Con `updates = {}` el f-string produce `MATCH (e:Epic {id: $id}) SET  RETURN e` — la
columna 38 es la `e` de `RETURN e` tras un `SET` sin expresiones → `CypherSyntaxError`.
Dos defectos colaterales en el mismo bloque:

- `updatedAt` se añade a `params` (línea 72) pero **nunca** a `set_clauses`: el nodo
  jamás actualiza su fecha con PATCH.
- `update_objective` (línea 136+) repite el mismo patrón — verificar al implementar
  (probablemente el mismo 500 con `{}`).

Este era precisamente el body que mandaba el smoke de la auditoría (el OpenAPI no
documenta `requestBody` → se manda `{}`, ver #595): `PATCH /epics/{id}` y
`PATCH /objectives/{id}` figuraban como ERR en la corrida run4.

## Status: DONE

## Priority: MEDIUM

## Component
Backend / Neo4j (mixin de epics/objectives)

## Type
bug fix / backend

## Implementation

1. **SET seguro** (`epic_mixin.py` `update_epic` y `update_objective`):
   - Incluir siempre `e.updatedAt = $updatedAt` (la key ya está en `params`) en las
     cláusulas SET → el body vacío al menos renueva `updatedAt` y la query es válida.
   - Defensa explícita: si `updates` viene vacío y aun así no queremos escribir nada,
     cortar antes de construir la query (o devolver 422 desde el router con
     `detail="empty update"`), en lugar de mandar Cypher inválido.
   - Validar/claves: `set_clauses` interpola `key` a pelo en la query — excluir keys
     que no sean identificadores seguros (inyección de Cypher vía nombre de campo).
2. **Router** (`routers/epic.py:208+`, `routers/objective.py:208+`): decidir contrato —
   body vacío → 422 con envelope `APIResponse` de validación, no 500.
3. **Tests**:
   - `test_patch_epic_empty_body_does_not_500` (422 o 200 con `updatedAt` nuevo, lo
     que se decida).
   - `test_patch_epic_with_fields_updates_and_touches_updated_at`.
   - Ídem para objectives.

## Acceptance Criteria
- [x] `PATCH /api/v1/epics/{id}` con `{}` → 422 controlado o 2xx con `updatedAt`
      actualizado (**nunca 500**)
- [x] `PATCH /api/v1/epics/{id}` con campos reales → 200 y los cambios persisten en
      Neo4j
- [x] `updatedAt` se renueva en toda actualización (hoy se envía el param y no se usa)
- [x] `update_objective` cubierto con el mismo arreglo (verificado, no asumido)
- [x] Las claves de `updates` no se interpolan a pelo en la query Cypher
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/neo4j_impl/epic_mixin.py` (líneas 69-79 y 136+)
- `src/socialseed_tasker/infrastructure/web_api/routers/epic.py` / `objective.py`
  (validación de body vacío)
- `tests/api/` — tests de PATCH

## Related Issues
- #578 (POST de epics/objectives → 500, mismo mixin), #595 (OpenAPI sin
  `requestBody` → el cliente auto-generado manda `{}`), #585 (familia Cypher),
  #594 (observabilidad de los 500)

## Notes
- **Repro**: `curl -X PATCH .../api/v1/epics/{id} -d '{}'` → 500 CypherSyntaxError;
  con `{"name":"x"}` → 200.
- Ojo: PATCH sobre un id inexistente devuelve 200 hoy (el MATCH no casa y no hay
  error) — decidir si se pasa a 404 en esta misma issue o queda fuera de alcance
  (documentarlo en los AC).

## Resolution (2026-10-21)

- **Contrato decidido**: body vacio en PATCH -> **422** (`HTTPException`, envelope
  `detail` estandar del repo) en `routers/epic.py` y `routers/objective.py` antes
  de tocar el repositorio. Body sin campos -> el cliente ve un error controlado,
  nunca un 500 de Cypher.
- **Mixin con defensa en profundidad** (`epic_mixin.py` `update_epic` /
  `update_objective`): allowlist de campos actualizables por entidad (Epic:
  `name/description/objective_id/status`; Objective: `name/description/status/
  quarter`). Claves fuera de la allowlist se descartan - sin interpolacion a pelo
  (AC de inyeccion) y ademas impide sobreescribir `id`/`createdAt` desde el body.
- Si tras filtrar no queda nada (updates vacio o solo claves invalidas) el mixin
  **no ejecuta ninguna query** -> imposible construir `SET  RETURN` invalido.
- `updatedAt` se anade SIEMPRE a las clausulas SET cuando hay updates reales
  (antes solo estaba en params y jamas se escribia).
- Fuera de alcance documentado: PATCH sobre id inexistente sigue devolviendo 200
  (MATCH no casa -> no-op silencioso); body con solo claves desconocidas -> 200
  sin efecto (el mixin las descarta). Ambos quedan pendientes si se quiere un
  contrato 404/422 estricto.
- Tests: `tests/unit/test_epic_objective_repo.py` (+8: vacio no query, SET con
  updatedAt, claves protegidas/desconocidas descartadas, solo invalidas -> no
  query; epic e objective) y `tests/api/test_epic_objective_patch.py` (5: 422 en
  vacio sin llamar al repo, 200 con campos, sin body -> 422).
- Gates: ruff 1004 (sin delta; tests nuevos limpios), mypy 1128 = 1128 verificado
  con `--no-incremental` (el 1129 puntual era ruido de cache incremental),
  pytest 1533 passed / 62 skipped / 0 failed (+13).
- Verificado en vivo (tasker-api reconstruida): PATCH epic/objective con `{}` ->
  **422**; con campos -> 200 y GET devuelve los cambios; Cypher confirma
  `createdAt != updatedAt`, `id`/`createdAt` intactos pese a los keys trampa
  (`id:"evil-id"`, `createdAt:"evil"` jamas escritos); `docker logs` sin ningun
  registro ERROR por estos 4 PATCH (junto a #594). Nodos borrados (0/0).
