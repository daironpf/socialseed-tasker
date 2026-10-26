# Issue #601: `GET /auth/me` fuera del envelope — migración coordinada con el frontend (`authApi.ts`)

## Description

`GET /api/v1/auth/me` devuelve el usuario **en plano**, sin el envelope
`{data, error, meta}` — confirmado en vivo el 2026-10-26:

```json
GET /api/v1/auth/me → 200
{"id":"admin","username":"admin","role":"ADMIN","permissions":["…"]}
```

Es el **único consumidor frontend directo** del patrón plano: `frontend/src/api/authApi.ts:57-61`

```ts
export async function fetchMe(): Promise<SessionUser> {
  const res = await authClient.get('/auth/me', { headers: bearerHeaders() })
  session.setUser(res.data as SessionUser)
  return res.data as SessionUser
}
```

`authClient` es una instancia axios **creada sin interceptors**
(`authApi.ts:14`) que no desempaqueta envelopes → si el backend se migra sin tocar el
frontend, `res.data` pasa a ser `{data, error, meta}` y `SessionUser` queda corrupto
(login/refresh/boot de la UI).

Por eso quedó **fuera del alcance del hallazgo #3** (decisión registrada en el
informe: *"no tocar `/auth/me` — 1 consumer frontend `authApi.ts:58-60`"*). Todo el
resto de la superficie (whoami, flags, data-quality, secrets, registry,
subscriptions) ya está migrado en #598; **este es el último endpoint de éxito en
plano**.

## Status: DONE

## Priority: MEDIUM

## Component
Backend / API (auth) + Frontend (capa de API/auth)

## Type
bug fix / backend + frontend

## Implementation

1. **Backend** — `routers/auth.py::me` (línea 310): cambiar la firma a
   `-> APIResponse[dict[str, Any]]` y devolver
   `data={id, username, role, permissions}` + `meta` — patrón idéntico al `whoami`
   migrado en `app.py` (#598). Los `HTTPException(401)` internos (missing bearer /
   invalid token / session revoked) **no cambian en esta issue**; quedarán enveloped
   cuando se cierre el handler de `HTTPException` de #599 (ordenar #599 antes si se
   quiere coherencia total, o aceptar el intermedio).
2. **Frontend** — `authApi.ts::fetchMe`: leer `res.data.data` (mejor: helper
   `unwrap<T>(res)` reutilizable si la capa `api/` ya tiene un patrón equivalente).
   Auditar **todos** los call-sites de `fetchMe` (arranque de la app, `authStore`,
   route guards) y los specs que mockeen `GET /auth/me`.
3. **Otros consumidores**: grep de `/auth/me` en `cli/` y `tests/` → actualizar o
   confirmar que solo lo consume el frontend (hoy: un único call-site).
4. **Tests**:
   - backend: envelope + `data` correcto con JWT (y 401 sin token intacto);
   - frontend: spec de `fetchMe` con respuesta enveloped (patrón de los `*.spec.ts`
     existentes de stores/api).
5. **i18n**: no aplica (sin textos nuevos).

## Acceptance Criteria
- [x] `GET /api/v1/auth/me` → 200 `{"data": {id, username, role, permissions},
      "error": null, "meta": {…}}`
- [x] `fetchMe()` del frontend desenvuelve el envelope y almacena el usuario (spec vitest verde)
- [x] Flujo de sesión validado; las regresiones de 401 sin/inválido/revocado permanecen
- [x] Búsqueda de `/auth/me` confirma que `authApi.ts::fetchMe` es el único consumidor frontend
- [x] Gates enfocados: pytest de autenticación, Vitest de auth y build frontend pasaron

## Resolution

`GET /api/v1/auth/me` ahora responde con `APIResponse` (`data`, `error`, `meta`).
`fetchMe()` lee `res.data.data`, guarda ese usuario en la sesión y lo devuelve.
Se añadieron pruebas para el envelope del backend y el desempaquetado/almacenamiento
en el frontend. Se auditaron las referencias a `/auth/me`; no hay consumidores
adicionales del body plano.

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/auth.py` (`me`)
- `frontend/src/api/authApi.ts` (+ su spec)
- `tests/` backend y specs frontend afectados

## Related Issues
- #598 (envelope de éxito — superficie restante), #599 (envelope de sus 401),
  #595 (OpenAPI), #527 (JWT y sesiones), #554/#552 (login real), hallazgo #3
  (alcance diferido a esta issue)

## Notes
- Confirmado en vivo 2026-10-26: body plano con JWT admin (`admintoken123`).
- Riesgo principal: interceptors — verificar primero si la capa `api/` del frontend
  tiene un unwrap global para otros clientes; `authClient` NO lo tiene (authApi.ts:14),
  así que el cambio frontend es prácticamente seguro.
