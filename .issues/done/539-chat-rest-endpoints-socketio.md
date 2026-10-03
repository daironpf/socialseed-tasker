# Issue #539: Endpoints REST del chat e integración con Socket.IO

## Description

Además del transporte en vivo (#538), el chat necesita una API REST versionada para operaciones CRUD y consultas históricas: listar conversaciones del usuario autenticado, crear conversaciones (directas o grupales) con `participant_ids` reales, paginar mensajes persistidos en MongoDB y fijar conversaciones. Todo mensaje creado por HTTP debe persistirse **e invocar la emisión en tiempo real** del evento Socket.IO `sio.emit('new_message', data, room=conversation_id)` para que los miembros de la sala lo reciban aunque el autor no esté conectado por socket.

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #4 (→ #539).

## Status: DONE (2026-10-02)

## Priority: MEDIUM

## Component
Backend / Chat / API

## Type
feat / backend

## Implementation
1. **Router `chat.py`:** nuevos endpoints bajo `/api/v1/chat/*` con el envelope `APIResponse` (camelCase) y el guard de autenticación existente (JWT/API key) del resto de la API.
2. **`GET /chat/conversations`:** retorna las conversaciones donde participa el `user_id` autenticado (repositorio #537), con `pinned_by`/último mensaje para el ordenado.
3. **`POST /chat/conversations`:** crea una conversación `direct` | `group` guardando los `participant_ids` reales del Auth Store; valida participantes duplicados/mínimos.
4. **`GET /chat/conversations/{id}/messages`:** recupera el histórico paginado (cursor por `created_at`/`_id` u offset) desde MongoDB; 403 si el usuario no es participante.
5. **`POST /chat/conversations/{id}/pin`:** marca/desmarca la conversación como fijada para el usuario (muta `pinned_by`).
6. **`POST /chat/conversations/{id}/messages`:** persiste el mensaje en MongoDB con `sender_id` = `user_id` del token y, a continuación, invoca la emisión en tiempo real compartida con #538: `sio.emit('new_message', data, room=conversation_id)` (dispatcher inyectable para tests sin servidor).

## Acceptance Criteria
- [x] `GET /api/v1/chat/conversations` retorna las conversaciones donde participa el `user_id` autenticado
- [x] `POST /api/v1/chat/conversations` crea una conversación (directa o grupal) guardando los `participant_ids` reales
- [x] `GET /api/v1/chat/conversations/{id}/messages` recupera los mensajes históricos paginados (cursor u offset) persistidos en MongoDB
- [x] `POST /api/v1/chat/conversations/{id}/pin` marca/desmarca una conversación como fijada para el usuario
- [x] Un mensaje creado vía `POST .../messages` se guarda en MongoDB e invoca la emisión Socket.IO `sio.emit('new_message', data, room=conversation_id)`
- [x] Gates backend sin regresiones

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/routers/chat.py`
- `tests/api/test_chat_endpoints.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/__init__.py` — exportación del router
- `src/socialseed_tasker/infrastructure/web_api/routes.py` — registro bajo `/api/v1`
- `src/socialseed_tasker/infrastructure/web_api/app.py` — dispatcher de emisión compartido con el servidor Socket.IO

## Related Issues
- #537 (repositorio MongoDB), #538 (servidor Socket.IO y dispatcher de emisión), #517 (arquitectura de API real), #527 (JWT/`user_id`)

## Verification (2026-10-02)

**Implementación**
- `routers/chat.py` (nuevo): los 5 endpoints bajo `/api/v1/chat/*` con envelope `APIResponse`;
  identidad vía JWT `sub` → token API-key → cookie OAuth → header `X-User-ID` (solo con
  `TASKER_AUTH_ENABLED=false`), 401 sin identidad; validaciones con `ValueError` → 400
  (tipo/duplicados/mínimos de participantes, cursor `before`, texto/tipo de mensaje);
  403 no participante / 404 inexistente / id malformado 400 / `ChatStoreError` → 503.
- Dispatcher de emisión compartido en `app.py`: `app.state.chat_emit` cierra sobre
  `app.state.chat_socket.sio.emit` (inyectable en tests: se sustituye por un recorder).
- `socketio_server.py`: proyecciones compartidas `conversation_wire`/`message_wire` —
  **todos** los payloads salientes (acks, `new_message`, `messages_read`, `typing_*` y REST)
  pasan a camelCase alineados con el tipo `ChatMessage` del frontend (#540: `content`,
  `senderId`, `readBy`, `createdAt`, `reactions` agrupadas `{emoji: [users]}`); entrada
  tolerante a `conversation_id`/`conversationId`. Derivación de #538 documentada aquí
  (los AC no fijaban forma de payload y #540 aún no consume el socket).
- `chat_repository.py`: nuevo `latest_message()` para el `lastMessage` de la lista.
- Export `chat_router` con re-export explícito (`as chat_router`, patrón `mcp_router`).

**Gates** (entorno `.venv`, cache mypy borrada; sin regresiones vs baseline 6840fc4):
- `ruff check src/` → **1011** (= baseline; ficheros nuevos limpios)
- `.venv\Scripts\python.exe -m mypy src/` → **1152 errores / 133 ficheros** (= baseline exacto;
  nota: `python -m mypy` con el intérprete global (numpy 2.5.1) aborta con un bloqueador
  preexistente de stubs — el gate válido es el `.venv`)
- `.venv\Scripts\python.exe -m pytest -q` → **1235 passed / 27 skipped / 3 failed**
  (= baseline 1226 + 9 tests nuevos: 8 de endpoints + `test_latest_message`; los 3 failed
  son los preexistentes `test_delivery_retries` + 2× `test_tasks_unit`)
- `tests/api/test_chat_endpoints.py` (nuevo, 8 tests): identidad/401, wires camel,
  validación de creación, paginación+403/404/400, pin, emisión con recorder inyectable,
  header dev, degradación 503.

**Smoke end-to-end** (`tasker-api:local` reconstruido, stack healthy, `smoke539.py` → **22/22**):
REST con JWT real + 2 clientes socket en la sala: `POST .../messages` por HTTP persistió en
Mongo **y** entregó `new_message` camel a ambos sockets (autor y no-autor); acks/`typing_*`/
`messages_read` camel; `lastMessage`, cursor `nextCursor`, pin toggle, 403/404/400/401.

**Documentación:** `features.md` §28 gana la subsección "Real API contract (#539)" (contrato
wire para #540).
