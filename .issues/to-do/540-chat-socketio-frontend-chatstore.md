# Issue #540: Conexión Socket.IO cliente y estado reactivo en frontend (chatStore)

## Description

El frontend Vue 3 debe hablar con el servidor Socket.IO (#538) para recibir mensajes en vivo, sincronizar indicadores de escritura y gestionar la reconexión, alternando entre modo Mock (fixtures actuales intactas) y Real según `apiMode` (#517). `notas.md` estandariza la librería **`socket.io-client`** con autenticación por token en el handshake y unión explícita a salas por conversación.

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #5 (→ #540).

## Status: TODO

## Priority: HIGH

## Component
Frontend / Chat / Realtime

## Type
feat / integration

## Implementation
1. **Dependencia:** `socket.io-client` en `frontend/package.json`.
2. **Módulo de conexión:** `frontend/src/api/chatSocket.ts` con un singleton `io(SOCKET_URL, { auth: { token } })` que envía el token JWT activo de `authStore`; `SOCKET_URL` deriva del mismo origen/base que la API real (`window.__API_URL__`); con gate `enabled` por `apiMode` al estilo de `realtime.ts` — en modo mock **nunca** se conecta.
3. **Ciclo de vida en `chatStore`:** conectar al entrar en modo real; al abrir una conversación `socket.emit('join_room', { conversation_id })` y `leave_room` al cambiar/cerrar; desconectar al logout.
4. **Listeners reactivos:**
   - `new_message` → inserta el mensaje en el listado de `ChatView.vue` y en `FloatingChat.vue` (unread badge incluido).
   - `typing_start` / `typing_stop` → actualiza `typingUsers` de forma reactiva; emisión propia con debounce al escribir en `ChatInput`.
   - `messages_read` → actualiza el estado de lectura de los mensajes.
   - `mark_as_read` emitido al visualizar la conversación.
5. **Reconexión resiliente:** manejar `connect`/`disconnect`/`reconnect` de socket.io (backoff nativo); mostrar el estado visual de la conexión en el header del chat (conectado/reconectando/desconectado); tras `reconnect` sincronizar los mensajes perdidos (`GET .../messages` desde el último `created_at` recibido).
6. **Mock intacto:** las fixtures y respuestas simuladas actuales de `chatStore` no cambian en modo mock.
7. **i18n:** estados de conexión EN + ES (ASCII en ES).

## Acceptance Criteria
- [ ] Dependencia `socket.io-client` añadida en `package.json`
- [ ] `chatStore` inicializa la conexión con `io(SOCKET_URL, { auth: { token } })` enviando el token JWT activo de `authStore`
- [ ] Unión y salida de salas con `socket.emit('join_room', { conversation_id })` / `leave_room`
- [ ] Evento `new_message` inserta reactivamente el mensaje en `ChatView.vue` y `FloatingChat.vue`
- [ ] Eventos `typing_start` / `typing_stop` actualizan la lista reactiva `typingUsers`
- [ ] Reconexión automática (`socket.on('reconnect')`), estado visual de la conexión en el header del chat y resincronización de mensajes perdidos tras un corte de red
- [ ] Conmutación por `apiMode` (mock sin conexión, real con socket); modo mock intacto
- [ ] i18n EN+ES; `npm run lint`, `npm test` y `npm run build` en verde

## Files to Create
- `frontend/src/api/chatSocket.ts`

## Files to Modify
- `frontend/package.json` / `package-lock.json` — `socket.io-client`
- `frontend/src/stores/chatStore.ts` — conexión, salas, listeners, reconexión
- `frontend/src/views/ChatView.vue` — mensajes reactivos + estado de conexión
- `frontend/src/components/chat/FloatingChat.vue` — mensajes reactivos en el widget
- `frontend/src/locales/en.json` / `es.json` — estados de conexión del chat

## Related Issues
- #538 (servidor Socket.IO), #539 (REST de conversaciones/mensajes para resync), #517 (toggle mock/real), #472/#504 (SSE previos), #477 (presencia/typing)
