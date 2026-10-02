# Issue #538: Servidor Socket.IO (python-socketio) con autenticación JWT

## Description

El chat necesita comunicación bidireccional en tiempo real con **salas (rooms)**, reconexión automática y eventos nombrados. En lugar de WebSockets nativos, la ÉPICA de `notas.md` estandariza el ecosistema **Socket.IO**: se integrará un servidor `python-socketio` en modo ASGI montado sobre la app FastAPI de `tasker-api`, con handshake autenticado por JWT (mismo token que #519/#527) y una sala por `conversation_id`. Este es el transporte que notificarán los REST (#539) y consumirá el frontend (#540).

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #3 (→ #538).

## Status: DONE (2026-10-02)

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
- [x] `python-socketio` (`AsyncServer`) acoplado a la app FastAPI mediante `socketio.ASGIApp`
- [x] `connect(sid, environ, auth)` valida el token JWT (`Bearer` o `auth['token']`) y extrae/verifica el `user_id` inalterable del claim
- [x] Conexión con token inválido o expirado → rechazo con error de autenticación
- [x] Salas con `sio.enter_room(sid, room=conversation_id)` tras validar el acceso del usuario
- [x] Eventos implementados: `join_room`, `leave_room`, `send_message`, `typing_start`, `typing_stop`, `mark_as_read`
- [x] `send_message` persiste en MongoDB y emite `new_message` a la sala; `mark_as_read` actualiza lectura y emite `messages_read`
- [x] Proxy nginx soporta el upgrade Socket.IO en `/socket.io/`
- [x] Gates backend sin regresiones

## Verification
- **Montaje:** `python-socketio 5.17.0` en `pyproject.toml`; `ChatSocketIOServer` (`AsyncServer(async_mode="asgi")`, CORS = `TASKER_FRONTEND_URL` + `TASKER_API_ALLOW_ORIGINS`, nunca `*` con envs del compose) creado en `create_app()` (`app.state.chat_socket`, repo compartido `app.state.chat_repository`); `__main__.py` envuelve con `chat_socket.asgi(app)` → `socketio.ASGIApp(sio, other_asgi_app=app)` en el CMD del contenedor (REST y `/socket.io/` mismo puerto/proceso). Handshake Engine.IO responde **fuera** del middleware API-key (verificado: polling `0{sid...}` sin 401) mientras REST sigue exigiendo la key (401 sin key ✓).
- **Handshake JWT:** `_extract_token` acepta `auth['token']` (crudo o con prefijo `Bearer`), header `HTTP_AUTHORIZATION` y query `token`/`access_token`; `verify_access` (#519) exige firma+`typ=access`+exp; si el claim lleva `sid` se valida la sesión Redis (#527) igual que el middleware REST; token ausente/inválido/expirado → `ConnectionRefusedError("authentication failed")` + log WARNING sin volcar el token (verificado: `connect rejected (sid=...): invalid or expired token`).
- **Salas/acceso:** `_participant` valida sesión, formato ObjectId, existencia (nuevo `ChatMongoRepository.get_conversation`, +1 test → 17) y `user_id in participant_ids` → errores tipados `UNAUTHENTICATED`/`VALIDATION_ERROR`/`NOT_FOUND`/`FORBIDDEN`/`CHAT_UNAVAILABLE` en envelope `{data, error}`; `disconnect` limpia `sid→user_id`.
- **Eventos:** `join_room`/`leave_room` (`enter_room`/`leave_room`), `send_message` (persiste #537 + `emit new_message` a la sala), `typing_start`/`typing_stop` (emisión con `skip_sid` al resto), `mark_as_read` (repo + `emit messages_read`).
- **nginx:** `frontend/nginx.conf` gana `location /socket.io/` con `proxy_http_version 1.1`, `Upgrade`/`Connection 'upgrade'`, buffering off y timeouts 3600s hacia `tasker-api:8000`; imagen `tasker-board:local` reconstruida → contenedor ejecutando el nuevo config (`nginx -T` muestra el location) y `nginx -t` OK.
- **Gates:** `ruff check src/` = **1011** (baseline) ✓ · `mypy src/` = **1152/133** con caché fresco (221 ficheros, 0 errores nuevos) ✓ · `pytest -q` = **1226 passed / 27 skipped / 3 failed** (1225 + 1 test de `get_conversation`; solo preexistentes) ✓.
- **Smoke funcional (cliente `socketio.Client` real contra `127.0.0.1:8888`):** token inválido → rechazado; `Bearer` en auth → conectado; `join_room` ack `{joined:true}`; `send_message` ack con id + **1 evento `new_message`**; `typing_start` ack + **0 eventos propios** (`skip_sid`); `mark_as_read` ack + evento `messages_read` en sala; texto vacío → `VALIDATION_ERROR`; **carol (no participante) → `FORBIDDEN`**; `leave_room` ack; `/health` healthy y `/api/v1/issues` 200 con key durante todo el smoke.
- **Nota:** añadido `sio.on(...)` en lugar de `@sio.event` (decorador sin tipar rompía mypy strict `untyped-decorator` ×6).

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/socketio_server.py` — `AsyncServer`, handshake JWT, salas y eventos

## Files to Modify
- `pyproject.toml` — dependencia `python-socketio`
- `src/socialseed_tasker/infrastructure/web_api/app.py` — creación del servidor y wiring con el repositorio de chat
- `src/socialseed_tasker/infrastructure/web_api/__main__.py` — servir el ASGI envuelto (`socketio.ASGIApp`)
- `frontend/nginx.conf` — `location /socket.io/` con cabeceras de upgrade hacia `tasker-api`

## Related Issues
- #519 (JWT/OAuth2 y claims), #527 (sesiones/`user_id`), #472/#517 (arquitectura de streaming previa), #537 (repositorio Mongo), #536 (servicio Mongo)
