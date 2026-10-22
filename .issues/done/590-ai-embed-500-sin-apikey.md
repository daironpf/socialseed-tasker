# Issue #590: `POST /ai/issues/{id}/embed` → 500 con `{"detail":"400: OPENAI_API_KEY not configured"}` — status y detalle incoherentes

## Description

Generar el embedding de una issue sin la key de OpenAI devuelve un `500` que **en su
propio body** reconoce un `400` del upstream:

```
POST /api/v1/ai/issues/{issue_id}/embed -> 500
{"detail": "400: OPENAI_API_KEY not configured"}
```

(Verificado in-process 2026-10-21 con `app.debug=True`; en run4, ERR.)

Problemas:

1. **Status incorrecto**: una configuración ausente no es un error interno 500; es un
   `503` (servicio no configurado) o un `400` de contrato — el 500 dispara alarmas y
   oculta la causa real en dashboards.
2. **Envelope inconsistente**: el resto de la API devuelve
   `{"data":null,"error":{"code":...,"message":...},"meta":...}`; aquí sale un
   `{"detail": "..."}` plano (el `HTTPException` de FastAPI sin pasar por el envelope,
   ni siquiera el de `generic_error_handler` de #594).
3. El mensaje mezcla niveles (`"400: "` como prefijo de string) — nada de esto es
   legible para un cliente automático.

Mismo patrón que #589 (config de tercero ausente → 500) y #591 (dependencia
ausente → 500).

## Status: DONE (commit pendiente)

## Priority: MEDIUM

## Component
Backend / AI (embeddings)

## Type
bug fix / backend

## Implementation

1. **Mapear la ausencia de key** en el handler/embedding service:
   - Sin `OPENAI_API_KEY` → `503` con código de error semántico
     (`AI_NOT_CONFIGURED` / `OPENAI_API_KEY_MISSING`) y mensaje accionable
     ("OPENAI_API_KEY no configurada"), dentro del envelope `APIResponse`/estándar del
     router.
   - Decidir 503 vs 400 siguiendo la convención del repo (503 = degradación por
     config/servidor; el chat/otros módulos ya usan 503 con detalle — patrón
     `notifications store unavailable`).
2. **No propagar el "400:" del upstream como si fuera detalle nuestro**: si en algún
   modo sí hay key y OpenAI responde 400/429, traducir a un error propio (429 con
   envelope, 400 de validación) en vez de reenviar el texto crudo.
3. **Auditar los vecinos** del router `ai/*`: `POST /ai/.../embed` no es la única
   ruta que depende de la key (embedding backfill, similar-issues — este último con su
   propio bug #591) — aplicar el mismo guard donde haga falta.
4. **Tests**:
   - `test_embed_without_openai_key_returns_503_with_envelope` (monkeypatch de env).
   - `test_embed_error_response_uses_api_response_envelope`.

## Acceptance Criteria
- [x] `POST /api/v1/ai/issues/{id}/embed` sin `OPENAI_API_KEY` → **503** (o 400 según
      decisión) con envelope `APIResponse` y código semántico — ya no 500 con
      `{"detail":"400: ..."}`
- [x] El body de error sigue el envelope del resto de la API
- [x] Con key presente el flujo no se rompe (guard solo en ausencia)
- [x] Rutas vecinas `ai/*` con la misma dependencia cubiertas por el mismo guard
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- Router/servicio de embeddings (`routers/ai*.py` o `application/` — localizar el
  call que lanza `"400: OPENAI_API_KEY not configured"`)
- `src/socialseed_tasker/infrastructure/web_api/app.py` (si se centraliza el mapeo)
- `tests/api/` — tests de degradación AI

## Related Issues
- #589 (labels/sync, mismo patrón), #591 (APOC ausente → 500), #594 (envelope/genérico
  de errores), #593 (otras configs de entorno del compose)

## Notes
- **Repro**: `curl -X POST http://127.0.0.1:8888/api/v1/ai/issues/{id}/embed -H
  'X-API-Key: test-token'` → 500 con el texto del 400.
- El stack real **no** define `OPENAI_API_KEY` — la issue es del backend (comportamiento),
  no de añadir la key (eso es config de despliegue).

### Resolución (2026-10-22)

**Causa exacta**: `generate_issue_embedding` (`routers/ai_search.py`) lanzaba
`HTTPException(400, "OPENAI_API_KEY not configured")` **dentro** de un `try` cuyo
`except Exception` lo re-envolvía como `HTTPException(500, str(e))` →
`str(HTTPException)` = `"400: OPENAI_API_KEY not configured"`. El mismo wrapping
enmascaraba el 404 de issue inexistente como `500 "404: Issue not found"`.

**Fix** (3 ficheros):

- `application/exceptions.py`: nueva `AIServiceNotConfiguredError` (junto a
  `GraphPortError` y familia).
- `web_api/app.py`: handler registrado → **503** con envelope estándar
  `_error_response("AI_NOT_CONFIGURED", str(exc))` (mismo patrón que
  `GraphPortError` → `DATABASE_CONNECTION_ERROR`/503).
- `routers/ai_search.py::generate_issue_embedding`: guard de key con `.strip()`
  **antes** de cualquier lógica → `AIServiceNotConfiguredError`; se eliminó el
  `try/except Exception` completo: la 404 ya no se envuelve (queda 404 real) y los
  errores inesperados propagan a `generic_error_handler` (#594) → envelope
  `INTERNAL_ERROR` + `logger.exception`.

**Rutas vecinas `ai/*`** (AC 4): `search-context`, `search-similar-solutions` y
`backfill-embeddings` ya degradan explícitamente a resultados vacíos/cero cuando
no hay key/embedder (200, sin path a 500) — cubiertas por sus tests existentes
(`test_ai_rag.py`, `test_search_similar_solutions.py`); `similar-issues` tiene su
propio bug #591.

**Tests** `tests/api/test_ai_embed_degradation.py` (4): sin key → 503 con envelope
(`data: null`, `error.code = AI_NOT_CONFIGURED`, `meta.request_id`, sin prefijo
`400:`); issue desconocida con key → 404 (no 500); con key + embedding existente →
200 sin tocar OpenAI; error inesperado → envelope `INTERNAL_ERROR`.

**Verificación en vivo** (tasker-api reconstruido, 2026-10-22): 10/10 —
`POST /ai/issues/{id}/embed` → **503** (ya no 500) con
`{"data":null,"error":{"code":"AI_NOT_CONFIGURED","message":"OPENAI_API_KEY not
configured; set it to generate issue embeddings","details":{}},"meta":{...}}`,
sin `400:`, vecino `/ai/search-context` → 200, nodos 5 → 5, `docker logs` sin
ERROR/Traceback. (Flujo con key: solo tests — el stack no define la key.)

**Gates**: ruff en los 3 ficheros 4 = HEAD (fichero de tests limpio),
`mypy src/` 1117 (HEAD 1119, −2), `pytest -q` **1600 passed / 62 skipped /
0 failed**.
