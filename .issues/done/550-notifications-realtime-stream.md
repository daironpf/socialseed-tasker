# Issue #550: Eventos en tiempo real de notificaciones vía SSE (`/api/v1/notifications/stream`)

## Description

Transmitir notificaciones en tiempo real a los clientes conectados cuando ocurra un evento relevante (bienvenida, HITL, asignaciones, cambios de agente), emitiendo `notification_created` al usuario destino sin recargar ni hacer polling.

Contexto real del repo: existen dos transportes ya probados — (a) **SSE con `RealtimeHub`** en `routers/realtime.py` (#517: buffers, pub/sub asyncio, `event: ping` cada 15s, cabecera `X-Accel-Buffering: no`, nginx ya con `proxy_buffering off` para `/api/`) usado por `/issues/stream` (#530), `/issues/{id}/github-sync/stream` (#522) y `/mcp/tool-calls/stream` (#524); y (b) **Socket.IO** para el chat (#538). `notas.md` admite SSE "o extender el dispatcher de Socket.IO" — se elige **SSE reutilizando el patrón del hub**: mismo estilo que el resto de streams no-chat, sin tocar el servidor de salas del chat, y el handler puede invocarse directamente en tests (en este entorno `TestClient.stream` cuelga en todo endpoint SSE, lección de #524).

Origen: `notas.md` → Sistema de Notificaciones Real en MongoDB · Issue #4 (→ #550).

## Status: DONE (2026-10-04)

## Priority: HIGH

## Component
Backend / Realtime / SSE

## Type
feat / realtime

## Implementation
1. **Endpoint `GET /api/v1/notifications/stream` (SSE):** `event: connected` (+ snapshot de las últimas notificaciones del usuario) atómicamente antes de suscribirse al tráfico en vivo, luego `event: notification_created` con la notificación insertada (wire camelCase) y `event: ping` heartbeat cada 15s; cabecera `X-Accel-Buffering: no`.
2. **Fan-out por usuario:** registro de suscriptores por `user_id` derivado del JWT (mismo mecanismo de identidad que #548; rechazar sin token); solo el destino recibe su evento, con soporte para suscripciones globales (`user_id` `global`/`system`) si la notificación es de canal global.
3. **Emisión:** publicación en el hub desde el punto de inserción — el initialize de #549 y el router de #548 (creaciones futuras) notifican al insertar; un único punto de publicación para no duplicar emisiones.
4. **Limpieza:** desconexión limpia al cerrar la petición (suscriptor eliminado del hub, sin fugas ni handlers colgados) — patrón ya probado en los streams existentes.
5. **Tests:** invocar el handler del stream directamente (`stream_*(Request(scope))`, patrón de #524) — `connected` + recepción de `notification_created` + aislamiento entre usuarios + limpieza de suscriptores.

## Acceptance Criteria
- [x] El cliente recibe `notification_created` de forma reactiva al insertarse la notificación, sin recargar ni polling explícito
- [x] Solo el usuario destino (o los suscriptores globales) recibe el evento
- [x] Desconexión limpia sin fugas de memoria ni suscriptores colgados (cubierta por test)
- [x] Auth del stream coherente con el resto de la API (JWT/sesión; sin token → rechazo)
- [x] Gates backend sin regresiones

## Files to Create
- `tests/api/test_notifications_stream.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/notifications.py` — ruta `/notifications/stream` y publicación al insertar
- `src/socialseed_tasker/infrastructure/web_api/routers/realtime.py` — hub/registro de suscriptores de notificaciones si se extiende el `RealtimeHub`
- `tests/api/test_setup_endpoints.py` / `test_notifications_api.py` — verificación de emisión al crear (bienvenida)

## Notes

Implementación (2026-10-04):

- **Endpoint** `stream_notifications` en `routers/notifications.py`: `_current_user` (mismo JWT que #548 → 401 sin token) → `_hub(request)` → **suscripción primero** y snapshot después (una inserción que racea la query queda encolada: posible duplicado, nunca hueco; los frames igualmente emiten `connected`+snapshot antes que ningún evento vivo) → generador con `connected` (`{"userId", "snapshot": [...]}`, los 50 más recientes vía `_wire`), bucle `is_disconnected`/`queue.get` con `asyncio.wait_for(..., HEARTBEAT_SECONDS)` → `ping`, y `finally: unsubscribe`. Headers `_SSE_HEADERS` (`X-Accel-Buffering: no`) reutilizados de `realtime.py`.
- **Fan-out** extendiendo `RealtimeHub` (no registry nuevo): `publish_notification/subscribe_notifications/unsubscribe_notifications` sobre `_notif_subs: dict[user_id, list[Queue]]`, con `GLOBAL_NOTIFICATION_TOPICS = ("global", "system")` espejados **solo** cuando `payload["channel"] == "system"` (la bienvenida es `system`; los canales personalizados nunca se filtran a otros usuarios).
- **Punto único de publicación** `emit_notification_created(app, note)` en `notifications.py` (usa `_wire`): llamado por `_insert_welcome_notification` (#549, `setup.py`) tras `repository.insert` y reservado para las futuras creaciones del router (#548, aún sin POST); no-op mientras no exista hub en `app.state` (un cliente tardío cubre su histórico con el snapshot).
- **Snapshot best-effort** en vez de 503: si la tienda falta o lanza `NotificationStoreError`, el stream conecta con `snapshot: []` y loguea — en vivo no necesita Mongo, y negar la conexión perdería realtime junto con el histórico (la REST #548 sigue degradando a 503 para lectura).
- **Tests** (10 nuevos, todos verdes): `tests/api/test_notifications_stream.py` (9) invoca el handler directamente `stream_notifications(Request(scope, receive))` con `receive` falso (`http.request` sigue vivo, `http.disconnect` termina) — 401 handler + 401 `TestClient` sobre la ruta registrada, `connected`+snapshot con aislamiento y cabeceras, entrega reactiva `notification_created` con bob intacto, desconexión que desuscribe, degradación a `snapshot: []`, fan-out hub (destino + espejo system/global), y `emit` no-op/sin hub + wire camelCase; en `test_setup_endpoints.py`, `test_initialize_emits_welcome_event_to_open_stream` fija la emisión de la bienvenida (#549) sobre un suscriptor abierto. `test_notifications_api.py` no se tocó: #548 no tiene endpoint de creación, la cobertura de emisión vive en las dos suites anteriores.
- **Gates:** ruff `1011` (baseline), mypy `1153` (baseline), pytest `1323 passed, 3 failed preexistentes, 27 skipped` (+10 tests sobre los 1313 de partida).

## Related Issues
- #517 (RealtimeHub + SSE client), #530 (`/issues/stream` como plantilla), #522/#524 (streams por recurso + técnica de test), #548 (inserciones que emiten), #549 (bienvenida en vivo), #538 (alternativa Socket.IO descartada por alcance), #551 (suscripción desde el store)
