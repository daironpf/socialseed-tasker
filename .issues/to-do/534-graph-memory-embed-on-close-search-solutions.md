# Issue #534: Graph Memory — auto-embed al cerrar + `search-similar-solutions`

## Description

La infraestructura de embeddings existe: `EmbeddingPort.embed_text`/`embed_batch`, `update_issue_embedding`/`search_by_embedding` en `application/actions.py`, `POST /api/v1/ai/issues/{id}/embed` (embed manual) y `GET /api/v1/ai/similar-issues/{issue_id}`, además del índice vectorial nativo de Neo4j (#209) que ya consume el RAG Explorer (#524). Falta lo que pide la ÉPICA 6 de `notas.md`: generar el embedding **automáticamente cuando un issue pasa a `CLOSED`** y un endpoint `POST /ai/search-similar-solutions` para que los agentes consulten cómo se resolvieron problemas afines.

Origen: `notas.md` → ÉPICA 6 · Issue #13 (→ #534).

## Status: TODO

## Priority: MEDIUM

## Component
Backend / AI / RAG / Embeddings

## Type
feat / ai infrastructure

## Implementation
1. **Embed al cerrar:** hook en el cierre de issue (`close_issue` / `POST /issues/{id}/close`) que construya el texto solución (title + solution summary + detalle relevante) y llame a `update_issue_embedding`; idempotente (no re-embebe si el contenido no cambió).
2. **Degradación sin API key:** sin provider de embeddings (`OPENAI_API_KEY` ausente) loguear y continuar — el cierre del issue nunca falla por embeddings.
3. **`POST /api/v1/ai/search-similar-solutions`:** body `{query, threshold?, limit?}` → embed de la query + `search_by_embedding` sobre issues cerrados → devuelve soluciones/issues similares con score en envelope `APIResponse`, pensado para consumo por agentes/CLI.
4. **Backfill:** comando opcional para re-embeber los issues cerrados existentes.

## Acceptance Criteria
- [ ] Crear el índice vectorial sobre descripciones/soluciones (ya existe #209) y cubrir los issues cerrados
- [ ] Al pasar un issue a `CLOSED` se genera y almacena el embedding de la solución (sin API key: degrada con log, cierre exitoso)
- [ ] `POST /ai/search-similar-solutions` devuelve soluciones similares con score por similitud de vector
- [ ] Backfill opcional para cerrar issues existentes
- [ ] Tests unit (embed on close + endpoint); gates backend sin regresiones

## Files to Create
- `tests/unit/test_embedding_on_close.py`
- `tests/api/test_search_similar_solutions.py`

## Files to Modify
- `src/socialseed_tasker/application/actions.py` — hook de embed en `close_issue`
- `src/socialseed_tasker/infrastructure/web_api/routers/ai_search.py` — `POST /search-similar-solutions`
- `features.md` — §68/§50

## Related Issues
- #192 (Vector indexing reasoning), #209 (RAG native Neo4j vector indexes), #208 (Code as graph), #301 (Embedding adapter), #228 (RAG embedding optimization), #524 (RAG Explorer real)
