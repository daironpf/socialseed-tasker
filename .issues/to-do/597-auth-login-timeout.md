# Issue #597: `GET /auth/login` (ruta sin prefijo `/api/v1`) no contesta — timeout contra el proxy OAuth `:4180`

## Description

En el inventario de las 294 rutas del backend real, `GET /auth/login` es el **único
TIMEOUT** de toda la corrida (run4 del smoke, 2026-10-20): la petición no devuelve
nada dentro del plazo (sin status, sin body):

```
TIMEOUT GET /auth/login
```

Mientras tanto, el login que sí se usa funciona:
`POST /api/v1/auth/login {"api_key": ...}` → `200` con JWT.

**Diagnóstico**: la ruta `GET /auth/login` (a diferencia del resto de la API, **sin**
el prefijo `/api/v1`) redirige hacia un servicio OAuth en el puerto **`:4180`** (proxy
OAuth) que no está resuelto/disponible en el entorno → la conexión queda colgada hasta
el timeout del cliente. O sea: o es una ruta legacy que apunta a un servicio que el
stack no levanta, o es un redirect a un host externo mal configurado.

Afecta a: clientes/openapi-consumers que prueban la superficie completa (el smoke la
marca TIMEOUT), y a cualquiera que espere que toda ruta publicada responda.

## Status: OPEN

## Priority: LOW

## Component
Backend / Auth (ruta legacy) + infra (proxy OAuth `:4180`)

## Type
bug fix / config

## Implementation

1. **Diagnóstico preciso**: localizar el handler de `GET /auth/login` (fuera del
   router `/api/v1` — revisar registro en `app.py`) y confirmar adónde redirige
   (`:4180`, host, path). Reproducir con `curl -v --max-time 5` para ver la Location.
2. **Decidir destino**:
   - **a) Es legacy/muerta** → eliminarla de la superficie pública (y del OpenAPI) o
     responder `410 Gone` / `404` controlado.
   - **b) Es el flujo OAuth real** → añadir el servicio `:4180` al
     `docker-compose.yml` (o apuntar al host/URL correcta vía env) y que la ruta
     responda con la redirección (302) en lugar de colgarse.
   - **c) Solo documentación** → si por diseño depende de un externo, que OpenAPI lo
     marque y el smoke la skippee con nota (no TIMEOUT silencioso).
3. **Test**: la ruta responde (302/404/200 según la opción elegida) en un plazo
   razonable — nunca timeout.

## Acceptance Criteria
- [ ] `GET /auth/login` → respuesta determinista (302 con Location, 404/410, o 200) en
      < 5s — ya no TIMEOUT
- [ ] Decisión reflejada en el stack (servicio compuesto / ruta retirada / OpenAPI
      documentado)
- [ ] `POST /api/v1/auth/login` sigue en 200 (regresión cero del login real)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` (registro de la ruta
  `GET /auth/login` fuera de `/api/v1`)
- El handler OAuth correspondiente
- `docker-compose.yml` (solo si Opción b)
- `tests/api/` — test de respuesta de la ruta

## Related Issues
- #554/#552 (login por credenciales/master key — el flujo que sí funciona), #527 (JWT
  y sesiones), #593 (otra config de entorno no definida en compose), #595 (OpenAPI
  veraz)

## Notes
- **Repro**: `curl -v --max-time 5 http://127.0.0.1:8888/auth/login` → cuelga (sin
  respuesta) hasta el timeout.
- Dato del smoke: es el único TIMEOUT entre 294 rutas — el resto responde en < 8s.
