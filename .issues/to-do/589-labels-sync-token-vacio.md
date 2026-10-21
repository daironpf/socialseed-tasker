# Issue #589: `POST /labels/sync` → 500 `Illegal header value b'token '` cuando no hay `GITHUB_TOKEN`

## Description

Sincronizar labels con GitHub revienta con un `500` cuyo "detalle" es una excepción de
httpx filtrada:

```
POST /api/v1/labels/sync -> 500
{"detail": "Illegal header value b'token '"}
```

(Verificado in-process 2026-10-21 con `app.debug=True` dentro de `tasker-api`;
también en run4. En el proceso local sin repositorio Neo4j la misma ruta falla
distinto: `'NoneType' object has no attribute 'sync_labels_from_github'` — dos
variantes del mismo endpoint desatendido.)

**Causa raíz**: el cliente de GitHub construye la cabecera
`Authorization: token <GITHUB_TOKEN>` con el **token vacío** (env `GITHUB_TOKEN` no
definida en `docker-compose.yml` ni en el entorno) → httpx valida las cabeceras y lanza
`Illegal header value` **antes** de salir a la red; el handler no lo atrapa → 500
genérico. De fondo hay dos warnings/diagnósticos ignorados:

- `application/secret_manager.py`: `No GitHub token configured for repo: ` (log WARNING
  visto en la repro).
- El modo sin repo (driver/repositorio `None`) ni siquiera llega a lo anterior:
  `sync_labels_from_github` solo existe como mixin del repositorio Neo4j
  (`neo4j_repository.py` — `LabelRepositoryMixin`), y el call-site asume que siempre
  está.

O sea: la ausencia de configuración de terceros se reporta como **bug interno 500** en
lugar de un estado controlado.

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / Labels (sync con GitHub)

## Type
bug fix / backend

## Implementation

1. **Guard de configuración** en el handler de `POST /labels/sync`
   (`routers/labels.py` — el call está en torno a la línea 152):
   - Sin `GITHUB_TOKEN` → `503` (o `400`) con envelope estándar:
     `{"code": "GITHUB_TOKEN_NOT_CONFIGURED", "message": ...}` — nunca dejar escapar
     `Illegal header value`.
   - Validar con `strip()` (token solo espacios también cuenta como ausente).
2. **Guard de repositorio**: si el repositorio/subyacente es `None` (modo sin Neo4j /
   sin adapter), responder `503 "Neo4j not available"` con el patrón del resto de
   routers en lugar de `AttributeError` sobre `None`.
3. **Cabeceras defensivas**: construir `headers` solo con la key si hay valor
   (no montar `f"token {os.environ.get(...)}"` a ciegas).
4. **Tests**:
   - `test_labels_sync_without_token_returns_503_not_500`.
   - `test_labels_sync_without_repository_returns_503`.
   - (Opcional, marcado/skip) `test_labels_sync_happy_path` con token fake y cliente
     inyectado.

## Acceptance Criteria
- [ ] `POST /api/v1/labels/sync` sin `GITHUB_TOKEN` → 503/400 con código claro, ya no
      500 `Illegal header value`
- [ ] Sin repositorio/driver → 503 con el patrón del resto (no `AttributeError`)
- [ ] Con token presente, la sincronización no se rompe por el guard (regresión happy
      path cubierta por test con cliente fake)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/labels.py` (handler de sync,
  ~línea 152)
- El módulo que construye la cabecera `Authorization: token ...` (cliente GitHub)
- `tests/api/` — tests de degradación

## Related Issues
- #590 (mismo patrón: config de tercero ausente → 500 en `ai/embed`), #591 (APOC
  ausente → 500), #594 (observabilidad), #593 (config del stack en compose)

## Notes
- **Repro**: `curl -X POST http://127.0.0.1:8888/api/v1/labels/sync -H 'X-API-Key:
  test-token'` → 500 `{"detail":"Illegal header value b'token '"}`.
- El stack real **no** define `GITHUB_TOKEN` (decisión de config: añadirla a compose
  es otra issue — aquí se arregla que la ausencia no rompa).
