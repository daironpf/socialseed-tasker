# Issue #594: Los 500 no dejan ningún rastro en `docker logs` — `generic_error_handler` sin `logger.exception` y `app.debug` nunca activo

## Description

Durante la auditoría del backend real (run4: **38 endpoints en ERR**), diagnósticar
cualquier 500 fue imposible desde los logs: `docker logs tasker-api` solo muestra el
envelope genérico:

```json
{"error":{"code":"INTERNAL_ERROR","message":"An unexpected error occurred",
 "details":{"detail":null}}, ...}
```

sin excepción, sin traceback, sin pila. Para averiguar las causas raíz de #578-#592
hubo que **montar un script in-process** (`app.debug = True` + `TestClient`, copiado al
contenedor con `docker cp` y ejecutado con `docker exec`) — es decir, replicar
artesanalmente lo que el servidor debería registrar solo.

Dos deficiencias:

1. **`app.py:1196 generic_error_handler`** devuelve el envelope pero no hace
   `logger.exception(...)` (ni siquiera `logger.error(..., exc_info=True)`) → cero
   stack en el log. Ni request_id correlacionado con la excepción.
2. **`app.debug` nunca es `true`** en runtime (no hay env/flag que lo active) → ni el
   debug de Starlette aporta nada, y el handler acorta el detalle a `detail: null`.

Efecto: cada bug de la auditoría costó 15-30 min de repro dirigida en lugar de leer
una línea de log. Cualquier error futuro en producción es igual de invisible.

## Status: DONE

## Priority: HIGH

## Component
Backend / Web API (manejador global de errores + logging)

## Type
bug fix / backend

## Implementation

1. **`app.py` `generic_error_handler` (~línea 1196)**:
   - `logger.exception("unhandled error on %s %s (request_id=%s)", method, path, rid)`
     en la rama de excepción no controlada (con `exc_info` → traceback completo en
     logs JSON estructurados, el formato que ya emite el resto del repo).
   - Conservar el envelope `INTERNAL_ERROR` al cliente (**sin** filtrar el mensaje
     interno en la respuesta — seguir sin exponer detalles), pero el log sí debe tener
     todo.
   - Aprovechar para setear `request_id` en ambas partes (el meta ya lo genera).
2. **Repartir el resto de handlers**: revisar que los `HTTPException` de 4xx NO se
   logueen como error (no llenar logs de ruido) — solo 5xx/excepciones.
3. **Flag de debug** (decidir): expuesta por env (`TASKER_APP_DEBUG=1`, default off) o
   eliminar la dependencia de `app.debug` si el handler ya loguea todo (recomendado:
   loguear bien y no depender de debug).
4. **Tests**:
   - `test_unhandled_exception_logs_traceback` (caplog con un endpoint que lance
     `RuntimeError` → se registra el traceback + `INTERNAL_ERROR` al cliente).
   - `test_http_exception_4xx_not_logged_as_error`.

## Acceptance Criteria
- [x] Provocar un 500 (p.ej. cualquier bug de #578-#586 sin fix) deja el **traceback
      completo** en `docker logs tasker-api` con el `request_id` de la respuesta
- [x] El cliente sigue recibiendo `INTERNAL_ERROR` sin internos filtrados
- [x] Los 4xx controlados no ensucian el log como errores
- [x] La visibilidad no depende de `app.debug=True` manual
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/app.py` (handler ~1196, logger)
- `tests/api/` — tests de logging de errores

## Related Issues
- **Todas las issues de 500 de esta auditoría** (#578-#587, #589-#591) — esta es la
  que hace diagnóstico posible; #592/#593 (códigos de estado engañosos)

## Notes
- Patrón de repro que sirve de plantilla: `docker cp script.py tasker-api:/tmp/ &&
  docker exec tasker-api python /tmp/script.py` con `create_app(...)` +
  `app.debug = True` (scripts de la auditoría en el workspace temporal de la sesión
  2026-10-20/21).
- Los logs JSON del repo ya tienen estructura (`timestamp/level/logger/message`) — el
  traceback debe viajar dentro de `message` (multi-línea) o como campo propio, sin
  romper el parseo.

## Resolution (2026-10-21)

- `observability/logging.py` `JsonFormatter`: antes descartaba `exc_info` (pop en
  la lista de extras) - ahora emite `exception` (traceback completo vía
  `formatException`) y `stack` como campos propios del JSON, sin romper el parseo.
- `app.py` `generic_error_handler`: `logger.exception("unhandled error on %s %s
  (request_id=%s, exception=%s)", method, path, rid, exc_name)` en todas las ramas
  (500 genérico y 503 de base de datos). El `request_id` generado se inyecta en
  `meta.request_id` del envelope via `_error_response(..., request_id=...)` ->
  mismo id en la respuesta del cliente y en el log (correlacion).
- El cliente sigue recibiendo `INTERNAL_ERROR` con `detail: null` (solo se filtra
  el interno si `app.debug`); los handlers 4xx siguen sin loguear (sin ruido).
- `web_api/__main__.py`: `configure_root_logger()` explicito al arrancar el
  servidor (antes solo dependia de imports laterales tipo `get_logger`).
- Tests nuevos `tests/api/test_error_logging.py` (5): envelope sin internos,
  traceback+request_id en caplog, JsonFormatter->campo exception, 404 y ValueError
  4xx no generan registros ERROR.
- Gates: ruff 1004 (sin delta), mypy 1128 (baseline 1129, sin delta negativo),
  pytest 1520 passed / 62 skipped / 0 failed (+5).
- Verificado en vivo (tasker-api reconstruida): PATCH /epics/{id} con body vacio
  (bug #579 sin fix) -> 500 con `detail: null` y, en `docker logs`, registro JSON
  ERROR con el mismo request_id, `exception=CypherSyntaxError` y traceback de
  ~20KB que incluye el frame `epic_mixin`. Epic sonda borrado (entorno en 0).
