# Issue #541: Suite de pruebas unitarias, integración y Socket.IO del chat

## Description

Blindar la ÉPICA de chat: persistencia MongoDB (#536/#537), servidor Socket.IO (#538), endpoints REST (#539) y cliente frontend (#540). `notas.md` pide una batería de tests de backend (`pytest` + `pytest-asyncio`) y frontend (vitest / `@vue/test-utils`) que valide la autenticación por JWT, la transmisión por salas con **el TestClient de python-socketio**, la sanitización de PII previa al envío y el comportamiento del `chatStore` en modo real y mock. Los tests deben correr sin servicios externos (repositorio fake/memoria, convención del repo).

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #6 (→ #541).

## Status: DONE (2026-10-03)

## Priority: HIGH

## Component
Testing / Chat / Backend + Frontend

## Type
test / quality

## Implementation
1. **Endpoints REST (`pytest`):** tests de `/conversations` y `/messages` verificando que el `user_id` del token JWT usado en la petición **coincide** con el `sender_id`/`participant_ids` registrado (nunca se acepta autoría ajena); paginación, pin y 403 para no participantes.
2. **Conexión Socket.IO:** test de conexión e instanciación del servidor con el **cliente de prueba de python-socketio** (`socketio.test_client` sobre el `AsyncServer`, o transporte ASGI en memoria); handshake con token válido acepta y con token inválido/expirado rechaza.
3. **Transmisión de salas:** simular **2 clientes** Socket.IO unidos a la misma sala; cliente A emite `send_message` y se verifica que el cliente B recibe `new_message` con el payload persistido; también `typing_start`/`typing_stop` y `mark_as_read` → `messages_read`.
4. **Persistencia:** repositorio contra DB en memoria/fake (sin containers ni red en CI) cubriendo alta de conversación, paginación de mensajes e índices.
5. **Frontend (`vitest`):** unit tests de las acciones de `chatStore.ts` en modo real (socket simulado con mock de `socket.io-client`: join/leave, `new_message`, typing, reconexión) y en modo mock (fixtures sin conexión).
6. **Componentes:** tests de `ChatView.vue` y `ChatInput.vue` verificando la emisión de eventos de tipeo al presionar Enter y la **sanitización de PII previa al envío** (flujo `piiDetector` existente, sin enviar el texto sensible por el socket).
7. **Gates:** backend (`ruff`/`mypy`/`pytest`) y frontend (`lint`/`test`/`build`) sin regresiones.

## Acceptance Criteria
- [x] Tests backend (`pytest` + `pytest-asyncio`) de endpoints REST validando que el `user_id` del token JWT coincide con el autor registrado
- [x] Test de conexión e instanciación de Socket.IO usando el cliente de prueba (TestClient de python-socketio)
- [x] Test de transmisión de salas: 2 clientes en la misma sala, A emite y B recibe `new_message`
- [x] Unit tests de las acciones de `chatStore.ts` en modo real y mock
- [x] Tests de `ChatView.vue`/`ChatInput.vue` con emisión de eventos de tipeo y sanitización de PII previa al envío
- [x] Tests sin dependencias de servicios externos (Mongo fake/memoria) y gates backend/frontend en baseline

## Files to Create
- `tests/api/test_chat_socketio.py`
- `frontend/src/stores/chatStore.spec.ts`
- `frontend/src/views/ChatView.spec.ts`

## Files to Modify
- `pyproject.toml` — `pytest-asyncio` (si no está activado) y fixtures del cliente de prueba
- `tests/api/test_chat_endpoints.py` — ampliar con casos de autenticación de autoría (creada en #539)

## Related Issues
- #518 (suite de tests/CI del frontend), #536/#537 (Mongo), #538 (servidor Socket.IO), #539 (REST), #540 (cliente frontend)

## Verification (2026-10-03)

**Decisiones de implementación**
- **Transporte del "test client":** `python-socketio` 5.17 ya no publica `socketio.test_client` (se eliminó en v5 y `AsyncSimpleClient` usa red real). Se implementó el equivalente permitido por la issue ("o transporte ASGI en memoria"): `TestClient.websocket_connect('/socket.io/?EIO=4&transport=websocket')` sobre `socketio.ASGIApp` con framing EIO/SIO manual (OPEN `0`, connect `40{"token":…}`, eventos `42N[…]`, acks `43N[…]`, CONNECT_ERROR `44`). Nota: Starlette no envía `upgrade: websocket` por defecto, se pasa como header explícito.
- **pytest-asyncio / pyproject:** ya estaba activo (`asyncio_mode = "auto"`); no hizo falta modificar `pyproject.toml`. Todos los tests nuevos son síncronos (TestClient).
- **Autoría:** `MessageCreateRequest` solo acepta `text`/`type` (extras pydantic ignorados) → el spoof de `senderId`/`sender_id` por body no tiene efecto; con `Authorization` JWT presente el `X-User-ID` se ignora; creador de conversación siempre incluye el `sub` del JWT.
- **Cobertura añadida al repositorio fake:** `FakeChatRepository.mark_as_read` (reutilizado por el test de Socket.IO).

**Tests (12 nuevos)**
- `tests/api/test_chat_socketio.py` (10): handshake válido registra usuario; rechazo sin token / token inválido / token expirado (`_access_claims`+`_sign` con `exp` pasado) → `44` + `_users` vacío; `join_room` ack + `FORBIDDEN`/`NOT_FOUND`/`VALIDATION_ERROR`; 2 clientes → `send_message` persiste y `new_message` llega a ambos con payload idéntico al ack; `typing_*` llega al resto sin eco al emisor (frames antes del ack); `mark_as_read` → ack `matchedCount=2` + `messages_read` a ambos y `read_by` actualizado; validaciones `send_message` (texto vacio, tipo inválido, no participante); `POST REST` → `new_message` recibido por el cliente conectado (dispatcher `app.state.chat_emit` → servidor real).
- `tests/api/test_chat_endpoints.py` (+2): `test_message_authorship_always_follows_token_identity`, `test_conversation_creator_identity_always_follows_token`.

**Frontend (22 nuevos)**
- `frontend/src/stores/chatStore.spec.ts` (17): mock (fixtures sin socket, selección/envío local sin emisión, `notifyTyping` no-op, conmutación a real conecta+hidrata) y real con `socket.io-client` mockeado (`vi.hoisted`): apertura+hidratación, join/`mark_as_read`/carga con `limit=50` y re-join en `connect`, `leave_room` al cambiar, `new_message` (preview/unread/dedupe de eco), activa sin badge, typing (dedupe, auto-limpieza 7s con fake timers, payloads malformados), `messages_read`, `disconnect` → `reconnecting` + resync `limit=100` en `reconnect`, envío por API con dedupe y fallback offline (`senderId`=JWT `sub`), `typing_start` único + `typing_stop` a los 2s, vuelta a mock (desconecta + fixtures).
- `frontend/src/views/ChatView.spec.ts` (5): render de la conversación activa; `notifyTyping` al escribir y Enter envía texto recortado sin modal; PII crítica bloquea el envío, conserva el texto y la máscara `[REDACTED_SECRET]` se envía sin el PAN; cancelar mantiene el texto sin enviar; "Send Anyway" envía solo con confirmación.

**Gates (baseline)**
- Backend: `ruff check src/` **1011** (sin cambios), `mypy src/` **1152 errores / 133 ficheros** (sin cambios), `pytest -q` **1247 passed / 27 skipped / 3 failed** = baseline 1235 + 12 nuevos, con las 3 preexistentes (`test_delivery_retry` + 2× `test_tasks_unit`). Requiere Docker/Neo4j arriba (`tasker-db` healthy); con el daemon caído los tests `tests/integration/*` fallan por `ConnectionRefusedError` (entorno, no regresión).
- Frontend: `npm test` **237 passed / 30 ficheros** (baseline 215 + 22), `npm run lint` **0 errores / 2 warnings** preexistentes (`IssueDetailView`), `npm run build` verde.
- `features.md` §28: nueva subsección "Chat test suite (#541)".
