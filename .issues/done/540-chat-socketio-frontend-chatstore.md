# Issue #540: Conexión Socket.IO cliente y estado reactivo en frontend (chatStore)

## Description

El frontend Vue 3 debe hablar con el servidor Socket.IO (#538) para recibir mensajes en vivo, sincronizar indicadores de escritura y gestionar la reconexión, alternando entre modo Mock (fixtures actuales intactas) y Real según `apiMode` (#517). `notas.md` estandariza la librería **`socket.io-client`** con autenticación por token en el handshake y unión explícita a salas por conversación.

Origen: `notas.md` → Épica Chat en Tiempo Real y Persistencia MongoDB · Issue #5 (→ #540).

## Status: DONE (2026-10-03)

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
- [x] Dependencia `socket.io-client` añadida en `package.json`
- [x] `chatStore` inicializa la conexión con `io(SOCKET_URL, { auth: { token } })` enviando el token JWT activo de `authStore`
- [x] Unión y salida de salas con `socket.emit('join_room', { conversation_id })` / `leave_room`
- [x] Evento `new_message` inserta reactivamente el mensaje en `ChatView.vue` y `FloatingChat.vue`
- [x] Eventos `typing_start` / `typing_stop` actualizan la lista reactiva `typingUsers`
- [x] Reconexión automática (`socket.on('reconnect')`), estado visual de la conexión en el header del chat y resincronización de mensajes perdidos tras un corte de red
- [x] Conmutación por `apiMode` (mock sin conexión, real con socket); modo mock intacto
- [x] i18n EN+ES; `npm run lint`, `npm test` y `npm run build` en verde

## Verification

- **Gates frontend (2026-10-03):** `npm run lint` → 0 errores (2 warnings preexistentes en `IssueDetailView.vue`); `npm test` → **215 passed / 28 ficheros** (baseline 208 + 7 nuevos); `npm run build` → verde (`vue-tsc -b && vite build`).
- **Módulo** `frontend/src/api/chatSocket.ts`: singleton `io(origen, { path: '/socket.io/', auth: { token } })`, origen derivado de `window.__API_URL__` (fallback `/api/v1` → misma origin), gate `isMockMode()` (en mock nunca se llama a `io`), sin token → no conecta, `emitChatEvent` solo con socket conectado. Estados `connecting/connected/reconnecting/disconnected` (`connect`, `disconnect` con motivo `io client disconnect`, `connect_error`, `socket.io.on('reconnect')`).
- **Unit (`chatSocket.spec.ts`, `socket.io-client` mockeado):** gate mock, conexión única con JWT en `auth`, sin token, reenvío de `new_message`/`typing_*`/`messages_read`/`connect`/`reconnect` a los handlers, estados, emisión condicionada, teardown + reconexión.
- **`chatStore`:** ciclo de vida por `apiMode` + `authStore.user` (conectar/hidratar al aparecer la sesión, desconectar al perderla; logout recarga la página → el socket se cierra), `join_room`/`mark_as_read` al seleccionar y en `onConnect`, `leave_room` + limpieza de `typingUsers` al cambiar, `new_message` → `commitMessage` (dedupe por `id`, orden por `createdAt`, `lastMessage`, badge de no leídos, `mark_as_read` si activa), `messages_read` → `readBy`, `typing_*` con auto-limpieza de 7s y `typing_stop` por inactividad de 2s (`notifyTyping` desde ChatInput/FloatingChat), resync tras `reconnect` (`GET .../messages?limit=100` merge por `id`), hidratación `GET /chat/conversations`, envío real por `POST .../messages` (fallback local sin simulación de agente), conmutación a mock restaura fixtures con copias frescas.
- **Contrato #539:** mappers `conversation_wire`/`message_wire` → `Conversation`/`ChatMessage` (participantes desconocidos con fallback; `currentUserId` = `sub` del JWT con fallback `admin`, así los mocks no cambian). Sin `console.*` (convención del repo).
- **UI:** chip de conexión en el header de ChatView y en el estado vacío, punto de conexión en el widget FloatingChat, `is-own`/etiquetas "You" por `currentUserId` (idéntico en mock: `admin`), claves `chat.connectionConnected|Connecting|Reconnecting|Disconnected` EN+ES (ASCII en ES), debounce de `typing_start` al escribir. Proxy Vite `ws: true` para `/socket.io` en dev.
- **Fuera de alcance (documentado):** badge `/chat` de `pendingFeatures` (lo mantienen los specs, cierre en la épica); creación de conversaciones y pin siguen locales en modo real (no figuraban en la issue); paginación de histórico antiguo (cursor `before`) queda pendiente de UX de scroll.

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
