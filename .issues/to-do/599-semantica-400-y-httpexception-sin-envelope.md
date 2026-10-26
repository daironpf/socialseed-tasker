# Issue #599: Semántica engañosa de los 400 — "not found" → 400, ids inválidos → `VALIDATION_ERROR` y `HTTPException` fuera del envelope

## Description

La sonda de la auditoría (phase B, `endpoint_probe.json`, 2026-10-25) registró **4
respuestas clasificadas `OTHER-400`** con semántica incorrecta — el hallazgo #4 del
informe ("semántica 400"):

| Ruta | Status | Body observado | Problema |
|---|---|---|---|
| `GET /api/v1/analyze/component-impact/{id}` | 400 | `{"detail":"Component not found: probe-…"}` | "not found" debería ser **404**; además `{"detail"}` **rompe el envelope** |
| `GET /api/v1/analyze/impact/{id}` | 400 | envelope `VALIDATION_ERROR: badly formed hexadecimal UUID string` | filtra el texto crudo del parser UUID de Python |
| `GET /api/v1/chat/conversations/{id}/messages` | 400 | envelope `VALIDATION_ERROR: invalid conversation_id` | la sonda esperaba **404** (id malformado/inexistente) |
| `POST /api/v1/chat/conversations/{id}/pin` | 400 | igual que la anterior | `expectation` del probe: **404** |

**Causas raíz (verificadas en código):**

1. **Handlers que hacen `raise HTTPException(status_code=400, detail=…)` para
   condiciones que no son validación del cliente** (p.ej. `Component not found`) —
   y el `detail` sale como `{"detail": …}` porque **`app.py` no registra handler para
   `HTTPException`** (los `@app.exception_handler` existentes son: errores de dominio,
   `ValueError`, `RequestValidationError` y `Exception` — `app.py:1081-1192`).
2. **El handler global `ValueError` → 400 `VALIDATION_ERROR` con `str(exc)` crudo**
   (`app.py:1153`): cualquier `ValueError` (parseo de `UUID`/`ObjectId` en routers,
   errores de dominio) se etiqueta como error de validación **del cliente** aunque la
   semántica real sea "recurso inexistente" u otra.
3. Los routers `analyze` y `chat` no siguen el patrón ya decidido en **#592**:
   *id inválido/inexistente → 404 sin filtrar existencia* (allí aplicado a
   notificaciones).

**Impacto**: clientes y el propio smoke clasifican mal los errores (400 ≠ 404 rompe
lógica de reintentos/CRUD y las expectation de la sonda); un consumidor que espere
`error.code` no puede leer nada en `{"detail"}`; los mensajes crudos de Python se
filtran al exterior.

## Status: TODO

## Priority: MEDIUM

## Component
Backend / API (manejadores de error globales + routers analyze/chat)

## Type
bug fix / backend

## Implementation

1. **Inventario de call-sites**: grep de `HTTPException(status_code=400` y
   `HTTPException(400` en `src/` + `detail="…not found…"` → clasificar cada uno:
   validación real (400/422) vs recurso ausente (404) vs conflicto (409). Empezar
   por los 4 de la sonda (`analyze/component-impact`, `analyze/impact`, chat
   `messages` y `pin`).
2. **Handler global de `HTTPException` con envelope** (nuevo en `app.py`, patrón del
   `RequestValidationError` existente): mapear status → código
   (`401→UNAUTHORIZED`, `403→FORBIDDEN`, `404→NOT_FOUND`, `405→METHOD_NOT_ALLOWED`,
   `409→CONFLICT`, `400→VALIDATION_ERROR`) y responder
   `APIResponse(data=None, error={code,message,details}, meta={timestamp,request_id})`
   con `_error_response` + `request_id` correlacionado (no perder el trabajo de #594).
   - **Auditar consumidores de `.detail`** antes del corte: grep en
     `frontend/src/**`, `cli/**` y `tests/` → decidir corte limpio con actualización
     de consumidores (preferido) o dual-read temporal (`error.message` ∥ `detail`)
     documentado.
3. **Corregir la semántica puntual de la sonda**:
   - `analyze/component-impact` → 404: re-lanzar `ComponentNotFoundError` y dejar que
     su handler existente (`app.py:1088`) responda con envelope, en vez de
     `HTTPException(400)`;
   - `analyze/impact` → id malformado: 422 con `error.code=INVALID_PATH_PARAM` (o
     400 con mensaje normalizado) — **sin** exponer `badly formed hexadecimal UUID…`;
   - chat conversación → aplicar **#592**: id no-ObjectId/inexistente → **404**
     (`error.code=NOT_FOUND`), no 400 `VALIDATION_ERROR`.
4. **Normalizar el handler `ValueError`**: dejar de exponer `str(exc)` crudo en
   `message`; mapear a códigos conocidos (`INVALID_PATH_PARAM`,
   `VALIDATION_ERROR`) con mensaje genérico y el detalle seguro en `details`.
5. **Tests**: uno por cada caso de la tabla (status + `error.code` + envelope), test
   de contrato "todo `HTTPException` responde `{data,error,meta}`", y tests de los
   consumidores actualizados (frontend/CLI según la decisión).

## Acceptance Criteria
- [ ] `GET /analyze/component-impact/{id}` inexistente → **404** con envelope
      `error.code=NOT_FOUND` (antes 400 `{"detail"}`)
- [ ] `GET /analyze/impact/{id}` con id malformado → 422/400 con `error.code`
      específico y sin texto crudo del parser UUID en `message`
- [ ] `GET …/messages` y `POST …/pin` con `conversation_id` inválido → **404**
      envelope (patrón #592)
- [ ] Todo `HTTPException` de la API responde `{data, error, meta}` (test de contrato)
- [ ] Consumidores de `.detail` auditados y actualizados (o dual-read documentado)
- [ ] La sonda de regresión no vuelve a marcar `OTHER-400` en esas 4 rutas
- [ ] Gates: pytest sin fallas nuevas, mypy/ruff sin delta

## Files to Create
- `tests/api/test_error_semantics.py` (nombre orientativo)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` (handler `HTTPException` +
  normalización del handler `ValueError`)
- `src/socialseed_tasker/infrastructure/web_api/routers/` — routers `analyze*` y
  `chat.py` (semántica 404/422)
- Consumidores si aplica: `frontend/src/**`, `cli/**`
- `tests/`

## Related Issues
- #592 (patrón id inválido → 404 — **la regla a seguir**), #594 (tracebacks con
  `request_id` — no perderlos), #595 (OpenAPI veraz: documentar los códigos nuevos),
  #598 (el envelope de éxito de esta tanda; el de errores es este), hallazgo #4 del
  informe

## Notes
- Evidencia: `endpoint_probe.json` (`%TEMP%\opencode`, 2026-10-25) — 4 records con
  `class=OTHER-400` (status 400 en una sonda que espera 404/422).
- Orden recomendado: hacer **después de #598** (imagen nueva) y **antes de #603**
  (el smoke vuelve a medir estas 4 rutas).
