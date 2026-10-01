# Issue #541: Suite de pruebas unitarias, integración y Socket.IO del chat

## Description

Blindar la ÉPICA de chat: persistencia MongoDB (#536/#537), servidor Socket.IO (#538), endpoints REST (#539) y cliente frontend (#540). `notas.md` pide una batería de tests de backend (`pytest` + `pytest-asyncio`) y frontend (vitest / `@vue/test-utils`) que valide la autenticación por JWT, la transmisión por salas con **el TestClient de python-socketio**, la sanitización de PII previa al envío y el comportamiento del `chatStore` en modo real y mock. Los tests deben correr sin servicios externos (repositorio fake/memoria, convención del repo).

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #6 (→ #541).

## Status: TODO

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
- [ ] Tests backend (`pytest` + `pytest-asyncio`) de endpoints REST validando que el `user_id` del token JWT coincide con el autor registrado
- [ ] Test de conexión e instanciación de Socket.IO usando el cliente de prueba (TestClient de python-socketio)
- [ ] Test de transmisión de salas: 2 clientes en la misma sala, A emite y B recibe `new_message`
- [ ] Unit tests de las acciones de `chatStore.ts` en modo real y mock
- [ ] Tests de `ChatView.vue`/`ChatInput.vue` con emisión de eventos de tipeo y sanitización de PII previa al envío
- [ ] Tests sin dependencias de servicios externos (Mongo fake/memoria) y gates backend/frontend en baseline

## Files to Create
- `tests/api/test_chat_socketio.py`
- `frontend/src/stores/chatStore.spec.ts`
- `frontend/src/views/ChatView.spec.ts`

## Files to Modify
- `pyproject.toml` — `pytest-asyncio` (si no está activado) y fixtures del cliente de prueba
- `tests/api/test_chat_endpoints.py` — ampliar con casos de autenticación de autoría (creada en #539)

## Related Issues
- #518 (suite de tests/CI del frontend), #536/#537 (Mongo), #538 (servidor Socket.IO), #539 (REST), #540 (cliente frontend)
