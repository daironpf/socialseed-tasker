# Issue #538: Servidor Socket.IO (python-socketio) con autenticación JWT

## Description

El chat necesita comunicación bidireccional en tiempo real con **salas (rooms)**, reconexión automática y eventos nombrados. En lugar de WebSockets nativos, la ÉPICA de `notas.md` estandariza el ecosistema **Socket.IO**: se integrará un servidor `python-socketio` en modo ASGI montado sobre la app FastAPI de `tasker-api`, con handshake autenticado por JWT (mismo token que #519/#527) y una sala por `conversation_id`. Este es el transporte que notificarán los REST (#539) y consumirá el frontend (#540).

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #3 (→ #538).

## Status: TODO

## Priority: CRITICAL

## Component
Backend / Chat / Realtime Architecture

## Type
feat / architecture

## Implementation
1. **Dependencia y montaje:** `python-socketio` en `pyproject.toml`; `AsyncServer(async_mode="asgi")` acoplado a la app FastAPI mediante `socketio.ASGIApp` (el ASGI servido por uvicorn envuelve FastAPI, endpoint por defecto `/socket.io/`), de forma que REST y Socket.IO comparten puerto y proceso.
2. **Handshake autenticado:** handler `@sio.event connect(sid, environ, auth)` — token JWT desde `auth['token']` (compatibles con cabecera/query `Bearer`); verificar el token con la infraestructura existente (`auth/tokens.py`, #519) y extraer el `user_id` **inalterable** del claim; token inválido o expirado → rechazar la conexión con error de autenticación (equivalente a 401, sin aceptar `sid`).
3. **Salas:** `sio.enter_room(sid, room=conversation_id)` al unirse (validando que el `user_id` es participante de la conversación vía repositorio #537) y `sio.leave_room(sid, room=conversation_id)` al salir; limpieza de salas en `disconnect`.
4. **Eventos de servidor:**
   - `join_room` / `leave_room` — unión/salida de la sesión a la sala de una conversación tras validar acceso.
   - `send_message` — recibe el payload del mensaje, lo persiste en MongoDB (#537) y emite `new_message` a la sala (`room=conversation_id`).
   - `typing_start` / `typing_stop` — transmite presencia e indicación de escritura a los demás miembros de la sala.
   - `mark_as_read` — actualiza `read_by` de los mensajes y emite `messages_read` a la sala.
5. **CORS/seguridad:** `cors_allowed_origins` restringido al origen del board (nginx), sin volcar tokens en logs, sesiones registradas auditables.
6. **Proxy nginx:** `frontend/nginx.conf` gana un `location /socket.io/` con cabeceras `Upgrade`/`Connection` hacia `tasker-api` (el proxy HTTP actual no pasa el upgrade).

## Acceptance Criteria
- [ ] `python-socketio` (`AsyncServer`) acoplado a la app FastAPI mediante `socketio.ASGIApp`
- [ ] `connect(sid, environ, auth)` valida el token JWT (`Bearer` o `auth['token']`) y extrae/verifica el `user_id` inalterable del claim
- [ ] Conexión con token inválido o expirado → rechazo con error de autenticación
- [ ] Salas con `sio.enter_room(sid, room=conversation_id)` tras validar el acceso del usuario
- [ ] Eventos implementados: `join_room`, `leave_room`, `send_message`, `typing_start`, `typing_stop`, `mark_as_read`
- [ ] `send_message` persiste en MongoDB y emite `new_message` a la sala; `mark_as_read` actualiza lectura y emite `messages_read`
- [ ] Proxy nginx soporta el upgrade Socket.IO en `/socket.io/`
- [ ] Gates backend sin regresiones

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/socketio_server.py` — `AsyncServer`, handshake JWT, salas y eventos

## Files to Modify
- `pyproject.toml` — dependencia `python-socketio`
- `src/socialseed_tasker/infrastructure/web_api/app.py` — creación del servidor y wiring con el repositorio de chat
- `src/socialseed_tasker/infrastructure/web_api/__main__.py` — servir el ASGI envuelto (`socketio.ASGIApp`)
- `frontend/nginx.conf` — `location /socket.io/` con cabeceras de upgrade hacia `tasker-api`

## Related Issues
- #519 (JWT/OAuth2 y claims), #527 (sesiones/`user_id`), #472/#517 (arquitectura de streaming previa), #537 (repositorio Mongo), #536 (servicio Mongo)
