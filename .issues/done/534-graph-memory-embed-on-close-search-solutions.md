# Issue #534: Graph Memory — auto-embed al cerrar + `search-similar-solutions`

## Description

La infraestructura de embeddings existe: `EmbeddingPort.embed_text`/`embed_batch`, `update_issue_embedding`/`search_by_embedding` en `application/actions.py`, `POST /api/v1/ai/issues/{id}/embed` (embed manual) y `GET /api/v1/ai/similar-issues/{issue_id}`, además del índice vectorial nativo de Neo4j (#209) que ya consume el RAG Explorer (#524). Falta lo que pide la ÉPICA 6 de `notas.md`: generar el embedding **automáticamente cuando un issue pasa a `CLOSED`** y un endpoint `POST /ai/search-similar-solutions` para que los agentes consulten cómo se resolvieron problemas afines.

Origen: `notas.md` → ÉPICA 6 · Issue #13 (→ #534).

## Status: DONE (2026-10-01)

## Priority: MEDIUM

## Component
Backend / AI / RAG / Embeddings

## Type
feat / ai infrastructure

## Implementation
1. **Embed al cerrar (`application/actions.py`):** nuevos helpers `build_solution_text(issue)` (title + resolution + description + commit, omitiendo partes vacías), `resolve_embedding_port()` (lazy import de `get_embedding_service` + `EmbeddingShim`; devuelve `None` si no hay proveedor o si el import falla — la capa aplicación no toma dependencias de infraestructura en import time) y `embed_issue_solution(repository, issue, embedder=None) -> bool` (nunca lanza: log + `False` en provider ausente, embedding vacío o error). `close_issue_action` ganó el parámetro opcional `embedder` y, tras persistir el cierre (fuera de la transacción), llama a `embed_issue_solution`.
2. **Sin doble embed:** se eliminó el bloque de embed de `neo4j_impl/issue_mixin.close_issue` (embebía `to_indexable_text` en cada cierre vía OpenAI); create/update siguen embebiendo en Neo4j. El hook vive ahora en un solo lugar: la acción de dominio. Idempotencia natural: `close_issue_action` es one-shot (`IssueAlreadyClosedError` en el segundo intento).
3. **`POST /api/v1/ai/search-similar-solutions`:** body `SimilarSolutionsRequest {query min_length=1, threshold 0..1 = 0.7, limit 1..50 = 10}` → embed de la query → `search_by_embedding` con overfetch `min(limit*3, 50)` → filtro endpoint-side `status == CLOSED` vía `get_issue` (el Cypher `SEARCH_BY_EMBEDDING` no filtra status) → resultados `{issue_id, title, score, resolution}`; sin proveedor o embed fallido → `data=[]` (mismo patrón degradado que `/search-context`).
4. **Backfill `POST /api/v1/ai/backfill-embeddings?force=`:** itera `list_issues(statuses=[CLOSED])`; por defecto solo los issues sin `description_embedding`, `force=true` re-embebe todos; devuelve `{embedded, skipped, failed, total_closed}`; sin proveedor → todo en 0.
5. **Degradación sin API key:** sin `OPENAI_API_KEY` el cierre nunca falla (log `solution embedding skipped/failed...`); search/backfill devuelven vacío.

## Acceptance Criteria
- [x] Crear el índice vectorial sobre descripciones/soluciones (ya existe #209) y cubrir los issues cerrados
- [x] Al pasar un issue a `CLOSED` se genera y almacena el embedding de la solución (sin API key: degrada con log, cierre exitoso)
- [x] `POST /ai/search-similar-solutions` devuelve soluciones similares con score por similitud de vector
- [x] Backfill opcional para cerrar issues existentes
- [x] Tests unit (embed on close + endpoint); gates backend sin regresiones

## Verification
- **Gates backend:** `ruff check src/` = **1011** (baseline) ✓ · `mypy src/` = **1151/133** (baseline) ✓ · `pytest -q` = **1199 passed / 27 skipped / 3 failed** (los mismos 3 preexistentes: `test_delivery_retries`, 2x `test_tasks_unit`; +15 tests nuevos) ✓
- **Tests nuevos (15):** `tests/unit/test_embedding_on_close.py` (8) — embed del texto solución completo, embedder que lanza → cierre OK, sin proveedor (monkeypatch) → sin embed, embedding vacío → no almacena, deps abiertas → no embebe, segundo cierre → idempotente, `build_solution_text` con partes mínimas/completas, `resolve_embedding_port` sin proveedor → None; `tests/api/test_search_similar_solutions.py` (7) — solo CLOSED en resultados, `limit` respetado, sin proveedor → `[]`, sin query → 422, backfill skip/embed/force/sin proveedor
- **Smoke live (tasker-api reconstruido):** `POST /api/v1/ai/search-similar-solutions` con query → 200 `data=[]` (sin `OPENAI_API_KEY` en el stack), sin query → 422 · `POST /api/v1/ai/backfill-embeddings` → `{embedded:0, skipped:0, failed:0, total_closed:0}` · OpenAPI expone ambas rutas ✓ · `POST /issues/{id}/close` sin proveedor → `CLOSED` (embed degradado, cierre exitoso) ✓ · `GET /api/v1/health` → `healthy` ✓ · auth sin key → 401 desde dentro del contenedor ✓
- **Nota (gate):** los dos `Depends(get_repo)` nuevos llevan `# noqa: B008` y las anotaciones son `APIResponse[list[Any]]`/`APIResponse[dict[str, Any]]` para mantener ruff/mypy exactamente en baseline (el estilo circundante `APIResponse[list]` + `Depends` sin noqa subiría los contadores).
- **Nota (fuera de alcance):** `IssueResponse` no expone el campo `resolution` en `GET /issues/{id}` (se almacena en el grafo y sí aparece en los resultados de `search-similar-solutions`); preexistente.
- **Frontend:** sin cambios en esta issue (solo backend) — gates FE no aplican.

## Files to Create
- `tests/unit/test_embedding_on_close.py`
- `tests/api/test_search_similar_solutions.py`

## Files to Modify
- `src/socialseed_tasker/application/actions.py` — `build_solution_text`, `resolve_embedding_port`, `embed_issue_solution`, hook + `embedder` en `close_issue_action`
- `src/socialseed_tasker/infrastructure/neo4j_impl/issue_mixin.py` — eliminado el embed de cierre (one-shot en la acción)
- `src/socialseed_tasker/infrastructure/web_api/routers/ai_search.py` — `POST /search-similar-solutions`, `POST /backfill-embeddings`
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` — `SimilarSolutionsRequest`
- `features.md` — §68/§50

## Related Issues
- #192 (Vector indexing reasoning), #209 (RAG native Neo4j vector indexes), #208 (Code as graph), #301 (Embedding adapter), #228 (RAG embedding optimization), #524 (RAG Explorer real)
