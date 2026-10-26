# Issue #600: `GET /api/v1/secrets` (colección) → 405 — existe el alta pero no el listado

## Description

`GET /api/v1/secrets` responde **405 Method Not Allowed con body vacío** — confirmado
en vivo el 2026-10-26 con JWT admin válido:

```
GET /api/v1/secrets  →  405 (cuerpo vacío)
GET /api/v1/auth/me  →  200 (referencia: sí responde)
```

Es el hallazgo #6 del informe de la auditoría. Causa: el router `secrets.py` registra
`POST /api/v1/secrets` (alta) pero **ningún `GET` en la colección**; Starlette hace
match del path contra la ruta `POST /secrets`, el método no coincide → 405 **sin
cuerpo** (ni siquiera envelope). Sin token el middleware devuelve 401 antes de rutear,
así que el 405 solo se ve autenticado.

Superficie actual (`routers/secrets.py`):

| Método | Ruta | Existe |
|---|---|---|
| POST | `/api/v1/secrets` | ✅ alta |
| GET | `/api/v1/secrets` | ❌ **405** |
| GET | `/api/v1/secrets/audit` | ✅ (#581) |
| GET | `/api/v1/secrets/{name}` | ✅ meta |
| GET | `/api/v1/secrets/{name}/value` | ✅ valor |
| DELETE | `/api/v1/secrets/{name}` | ✅ |
| POST | `/api/v1/secrets/rotate`, `/rotate/run` | ✅ |

Sin el `GET` de colección **no hay forma de listar los nombres de los secretos** sin
conocerlos de antemano (la auditoría es un evento, no un catálogo). Toda ruta publicada
debe responder de forma determinista — hoy la colección es un agujero 405.

## Status: TODO

## Priority: MEDIUM

## Component
Backend / API (secrets)

## Type
feat / backend

## Implementation

1. **Decidir el contrato** (dos opciones):
   - **A (recomendada)**: `GET /api/v1/secrets` → 200 `APIResponse[data=list]` con
     **metadatos** de cada secreto (nombre, created/updated, estado de rotación si
     existe) — **nunca valores**; reutilizar la proyección de `GET /secrets/{name}`
     (que ya es meta sin value).
   - **B**: si el listado no se quiere exponer, responder **404 controlado** (o 410)
     en lugar del 405 silencioso y dejar la decisión anotada en OpenAPI — decisión
     explícita, no accidental.
2. **Implementación de A**: handler `GET /api/v1/secrets` en `routers/secrets.py`
   con el **mismo guard que sus vecinos** — ojo: `secrets.py` es uno de los puntos
   que resuelven identidad desde `verify_token`+RBAC **sin fallback JWT**, marcado
   en la resolución de #593 como *"candidato para follow-up con
   `require_permission`"* → usar `require_permission(request, …)` consistente con
   `GET /secrets/audit`, no un guard nuevo.
3. **Orden de rutas**: registrar el `GET` exacto de colección **antes** de
   `GET /secrets/{name}` (precedente #581 del sombreado por `{name}`); aunque path
   exacto no compite con `{name}`, mantener el patrón de la casa.
4. **Envelope**: entrar directo con `{data, error, meta}` (migración ya hecha en
   #598 para el resto de `secrets`).
5. **Tests**:
   - 200 con lista enveloped y **cero valores** en el body (aserción anti-fuga);
   - 401 sin identidad / 403 sin permiso (mismo comportamiento que `/secrets/audit`);
   - 405 desaparecido;
   - contrato OpenAPI: `GET /secrets` declara `200` con schema (regresión del
     contrato de #595).

## Acceptance Criteria
- [ ] `GET /api/v1/secrets` con JWT → 200 envelope con nombres/metadata (0 valores
      de secreto en la respuesta)
- [ ] Sin identidad → 401; sin permiso → 403 (guard consistente con `/secrets/audit`)
- [ ] El 405 desaparece de la superficie y `openapi.json` documenta el `GET`
- [ ] `GET /secrets/{name}` y `GET /secrets/audit` sin regresión de ruteo
- [ ] Gates: pytest sin fallas nuevas, mypy/ruff sin delta

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/secrets.py`
- `tests/api/` — test del listado + contrato OpenAPI

## Related Issues
- #581 (sombreado de `/secrets/audit` por `/{name}` — precedente de orden de rutas),
  #593 (guard `require_permission` y la nota de follow-up de `secrets.py`), #595
  (contrato OpenAPI), #598 (envelope de la superficie secrets), hallazgo #6 del
  informe

## Notes
- Repro (2026-10-26): con JWT admin → `GET /api/v1/secrets` → 405 sin cuerpo; sin
  token → 401 del middleware (el 405 solo se ve autenticado).
- Si se elige la opción B, dejar constancia en la `Resolución` de por qué el listado
  no se expone.
