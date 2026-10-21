# Issue #581: `GET /secrets/audit` → 500 — la ruta está sombreada por `GET /secrets/{name}`

## Description

`GET /api/v1/secrets/audit` nunca alcanza su handler: devuelve `500` con
`AttributeError: 'list' object has no attribute 'get'`.

Traceback reproducido en vivo 2026-10-21 (`app.debug=True`, TestClient en el
contenedor):

```
GET /api/v1/secrets/audit -> 500
  routers/secrets.py:53 api_get_secret_meta     <-- handler equivocado
  secrets/core.py:69 get_secret
AttributeError: 'list' object has no attribute 'get'
```

**Causa raíz (doble):**

1. **Sombreado de ruta**: el handler literal `GET /secrets/audit` está declarado en
   `routers/secrets.py:113-119`, pero la plantilla `GET /secrets/{name}` (línea ~53,
   `api_get_secret_meta`) se registra **antes**, y FastAPI casa en orden de
   registro → la palabra `audit` se interpreta como el *nombre de un secreto*. El
   endpoint de auditoría real es inalcanzable (el traceback lo prueba: entra por
   `api_get_secret_meta`, no por `api_get_audit`).
2. **Tipo de dato**: al resolver `secrets:audit` como secreto, `SecretManager.get_secret`
   hace `entry: dict = json.loads(raw)` y luego `entry.get("metadata")`
   (`src/socialseed_tasker/secrets/core.py:59-70`), pero el valor almacenado en la
   clave de auditoría es un **JSON array** → `'list' object has no attribute 'get'`.

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / Secrets (routers + `SecretManager`)

## Type
bug fix / backend

## Implementation

1. **Orden de rutas** (`routers/secrets.py`):
   - Mover `@secrets_router.get("/api/v1/secrets/audit")` (línea 113) **encima** de la
     ruta con path-param `/{name}` (las literales primero), o renombrar la plantilla
     (p.ej. `/{name:path}` excluyendo `audit`, o un prefijo versionado).
   - Verificar el resto de literales del router contra `/{name}` (repasar el fichero
     entero: ¿hay más rutas declaradas después de la template?).
2. **`get_secret` tolerante** (`secrets/core.py:59-70`): si el JSON parseado no es un
   dict, fallar con `KeyError`/`ValueError` claro (o devolver la lista cruda donde
   haga falta) en vez de `AttributeError` — un formato inesperado en storage no debe
   ser 500 genérico.
3. **Tests**:
   - `test_secrets_audit_returns_200_and_list`: `GET /api/v1/secrets/audit` → 200
     `{"status": "ok", "audit": [...]}` (hoy es inalcanzable → siempre 500).
   - `test_get_secret_still_works_for_normal_names`: `GET /secrets/{name}` de un
     secreto real sigue respondiendo 200/404 esperado (no se rompe el sombreado al
     revés).

## Acceptance Criteria
- [ ] `GET /api/v1/secrets/audit` → 200 con `{"status":"ok","audit":[...]}` (lista de
      eventos de auditoría)
- [ ] `GET /api/v1/secrets/{nombre-real}` sigue resolviendo al handler de metadatos
      (sin regresión)
- [ ] Un secreto/clave con JSON no-dict no produce `AttributeError` → error tipado
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/secrets.py` (orden de
  declaraciones: `:53` vs `:113`)
- `src/socialseed_tasker/secrets/core.py` (líneas 59-70)
- `tests/api/` — tests de auditoría y de `/{name}`

## Related Issues
- #594 (los 500 no dejan traceback en `docker logs`), #595 (OpenAPI de secrets sin
  `requestBody` documentado)

## Notes
- **Repro**: `curl http://127.0.0.1:8888/api/v1/secrets/audit -H 'X-API-Key:
  test-token'` → 500.
- Verificado in-process 2026-10-21 con `app.debug=True` (el traceback identifica el
  handler por su línea exacta, no por el status).
