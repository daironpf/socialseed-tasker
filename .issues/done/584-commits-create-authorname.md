# Issue #584: `POST /commits` → 500 — atributo `authorName` inexistente en el modelo `Commit`

## Description

El alta de commits está rota: `POST /api/v1/commits` con body válido devuelve `500` y
no crea nada.

Traceback reproducido in-process 2026-10-21 (`app.debug=True`, contenedor
`tasker-api`):

```
POST /api/v1/commits {"sha": <40 hex>, "message": "dbg", "author_name": "dbg"} -> 500
  routers/commit.py:176 create_commit
  neo4j_commit_repository.py:55 create_commit
AttributeError: 'Commit' object has no attribute 'authorName'. Did you mean: 'author_name'?
```

**Causa raíz**: `Neo4jCommitRepository.create_commit`
(`src/socialseed_tasker/infrastructure/neo4j_commit_repository.py:48-64`) escribe
`commit.authorName` (estilo camelCase de la query/alambrado) pero la entidad Pydantic
`Commit` de dominio expone `author_name` (Pydantic sugiere el nombre snake_case).
Mismo patrón exacto que `POST /epics`/`POST /objectives` (#578) — camelCase asumido en
los repositorios Neo4j contra modelos snake_case.

La entidad `Commit` ya se construye correctamente en sentido inverso en
`_node_to_commit` (línea 20+), o sea que el roundtrip de **lectura** funciona; lo roto
es la **escritura**.

Relacionado: `POST /commits/{sha}/link/agent/{agent_id}` también da 500 en el smoke
run4, pero por otra causa (parámetro `$agentId` vs `agent_id=`) → está cubierto en
**#585**.

## Status: DONE

## Priority: MEDIUM

## Component
Backend / Neo4j (repositorio de commits)

## Type
bug fix / backend

## Implementation

1. **Fix de mapeo** (`neo4j_commit_repository.py:48-64`): usar los campos reales de la
   entidad `Commit` (`author_name`, etc. — auditar **todos** los accesos camelCase del
   método: `authorName` puede no ser el único: revisar `committerName`, `authoredAt`,
   `committedAt`… contra `domain/` y contra los nombres de propiedad que espera la
   query `CREATE_COMMIT`).
   Si la query Cypher usa nombres camelCase (p.ej. propiedades `authorName` en el
   nodo), mapear **en el repo**: atributo snake_case del modelo → nombre de propiedad
   de la query (un solo punto de traducción, igual que `_node_to_commit` a la inversa).
2. **Router** (`routers/commit.py:149-176`): verificar que el body que llega
   (`CommitCreate`/equivalente) construye la entidad con todos los campos requeridos.
3. **Tests**:
   - `test_create_commit_roundtrip`: POST 201 → `GET /commits/{sha}` devuelve el commit
     con `author`/mensaje correctos.
   - Test del repo con driver fake que fija los kwargs/nombres de propiedad que
     recibe `session.run`.

## Acceptance Criteria
- [x] `POST /api/v1/commits` con sha/mensaje/autor → 2xx (ya no 500) y `GET
      /api/v1/commits` lo lista; `GET /commits/{sha}` lo devuelve
- [x] El nodo en Neo4j tiene las propiedades con los nombres que espera
      `_node_to_commit` al leer (roundtrip completo)
- [x] Ningún acceso camelCase a atributos Pydantic en `neo4j_commit_repository.py`
      (revisión completa del fichero, no solo la línea 55)
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/neo4j_commit_repository.py` (líneas 48-64)
- `src/socialseed_tasker/infrastructure/neo4j_queries.py` (solo si hay que alinear
  nombres de propiedades CREATE_COMMIT)
- `tests/api/` — roundtrip de commits

## Related Issues
- #578 (mismo bug en epics/objectives), #585 (`link/agent` de commits → 500 por
  parámetros), #594 (observabilidad), #595 (OpenAPI)

## Notes
- **Repro**: `curl -X POST http://127.0.0.1:8888/api/v1/commits -H 'X-API-Key:
  test-token' -H 'Content-Type: application/json' -d '{"sha":"<40 chars>","message":"t",
  "author_name":"t"}'` → 500.
- El smoke de auditoría ya generaba sha únicos (`BODY_OVERRIDE` de `smoke_real.py`) y
  aun así recibía 500 — no es problema de duplicado.

## Resolution (2026-10-21)

- `neo4j_commit_repository.py create_commit`: los 4 accesos camelCase pasaron a
  snake_case (`author_name`, `author_email`, `is_ai_generated`, `files_changed`).
  Los params ya eran snake y la query `CREATE_COMMIT` los mapea a props camel
  (`authorName: $author_name`) - alineado con la lectura `_node_to_commit`.
- **Segundo crash latente encontrado en la auditoria exigida por el AC**:
  `routers/commit.py _commit_to_response` (usado por POST, GET /commits/{sha} y
  GET /commits) leia `commit.authorName/authorEmail/isAiGenerated/filesChanged`
  - sin arreglarlo, el POST seguia en 500 incluso tras fix del repo. Corregido a
  snake_case (4 accesos, lineas 130-139).
- Auditoria completa de ambos ficheros: ningun otro acceso camelCase a atributos
  Pydantic (los `node.get("authorName")` del path de lectura son correctos).
- El router construye `Commit` con kwargs alias camelCase (`authorName=`...) -
  valido gracias a `populate_by_name=True`/`alias_generator` de la entidad; se
  dejo tal cual (no es bug) para no tocar mas del necesario.
- POST /commits responde **200** (la ruta no fija status_code; el AC pedia 2xx).
- Tests `tests/api/test_commit_roundtrip.py` (3): contrato de kwargs snake de
  `session.run` con driver grabador, roundtrip API completo POST -> GET sha ->
  GET lista -> DELETE -> 404 con driver fake que emula CREATE_COMMIT, y 404 de
  commit inexistente.
- Gates: ruff 1004 (sin delta; test limpio), mypy **1128 -> 1124** (`--no-incremental`,
  el fix elimina 4 attr-defined), pytest 1536 passed / 62 skipped / 0 failed (+3).
- Verificado en vivo (tasker-api reconstruida): POST /commits -> 200 con datos,
  GET /commits/{sha} y GET /commits -> 200 roundtrip completo, DELETE -> 200 y
  GET posterior -> 404; nodo en Neo4j con props camelCase (`authorName`,
  `authorEmail`, `isAiGenerated`, `filesChanged`); `docker logs` con 0 registros
  ERROR. Commits de prueba borrados (0).
