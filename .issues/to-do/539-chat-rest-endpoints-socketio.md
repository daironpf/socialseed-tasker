# Issue #539: Endpoints REST del chat e integración con Socket.IO

## Description

Además del transporte en vivo (#538), el chat necesita una API REST versionada para operaciones CRUD y consultas históricas: listar conversaciones del usuario autenticado, crear conversaciones (directas o grupales) con `participant_ids` reales, paginar mensajes persistidos en MongoDB y fijar conversaciones. Todo mensaje creado por HTTP debe persistirse **e invocar la emisión en tiempo real** del evento Socket.IO `sio.emit('new_message', data, room=conversation_id)` para que los miembros de la sala lo reciban aunque el autor no esté conectado por socket.

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #4 (→ #539).

## Status: TODO

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
- [ ] `GET /api/v1/chat/conversations` retorna las conversaciones donde participa el `user_id` autenticado
- [ ] `POST /api/v1/chat/conversations` crea una conversación (directa o grupal) guardando los `participant_ids` reales
- [ ] `GET /api/v1/chat/conversations/{id}/messages` recupera los mensajes históricos paginados (cursor u offset) persistidos en MongoDB
- [ ] `POST /api/v1/chat/conversations/{id}/pin` marca/desmarca una conversación como fijada para el usuario
- [ ] Un mensaje creado vía `POST .../messages` se guarda en MongoDB e invoca la emisión Socket.IO `sio.emit('new_message', data, room=conversation_id)`
- [ ] Gates backend sin regresiones

## Files to Create
- `src/socialseed_tasker/infrastructure/web_api/routers/chat.py`
- `tests/api/test_chat_endpoints.py`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/__init__.py` — exportación del router
- `src/socialseed_tasker/infrastructure/web_api/routes.py` — registro bajo `/api/v1`
- `src/socialseed_tasker/infrastructure/web_api/app.py` — dispatcher de emisión compartido con el servidor Socket.IO

## Related Issues
- #537 (repositorio MongoDB), #538 (servidor Socket.IO y dispatcher de emisión), #517 (arquitectura de API real), #527 (JWT/`user_id`)
