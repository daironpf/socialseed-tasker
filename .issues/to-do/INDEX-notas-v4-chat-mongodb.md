# Chat Real & MongoDB Backlog — Issue Index

**Source:** `notas.md` (v4 — Épica: Chat en Tiempo Real y Persistencia MongoDB, estrategia Socket.IO)
**Created:** 2026-10-01
**Status:** TODO (3/6 done: #536, #537, #538)

> `notas.md` (v4) define las issues como [ISSUE-CHAT-01]…[ISSUE-CHAT-06]; el siguiente
> número libre en `.issues/done` era **#536** (máximo actual #535), por lo que se
> numeraron **#536–#541** conservando el orden y contenido del plan original. La ÉPICA
> estandariza **Socket.IO** de forma explícita (`python-socketio`/`socket.io-client`,
> salas nativas, reconexión resiliente y eventos nombrados) en lugar de WebSockets
> nativos. La UI de chat (ChatView, FloatingChat, chatStore con PII) ya existe en modo
> mock; este backlog la dota de persistencia MongoDB y transporte Socket.IO real.
> Como en los backlogs anteriores, los ficheros de issue viven en `.issues/to-do/`
> hasta que se implementan (se mueven a `.issues/done/` con `Status: DONE`).

---

## Issue Index

| # | Issue | Priority | Type | Status | notas.md |
|---|---|---|---|---|---|
| #536 | Servicio Docker MongoDB para chat | HIGH | infra / devops | DONE (→ `.issues/done/`) | [ISSUE-CHAT-01] |
| #537 | Esquema del modelo y repositorio MongoDB del chat | HIGH | feat / backend | DONE (→ `.issues/done/`) | [ISSUE-CHAT-02] |
| #538 | Servidor Socket.IO (python-socketio) con autenticación JWT | CRITICAL | feat / architecture | DONE (→ `.issues/done/`) | [ISSUE-CHAT-03] |
| #539 | Endpoints REST del chat e integración con Socket.IO | MEDIUM | feat / backend | TODO | [ISSUE-CHAT-04] |
| #540 | Conexión Socket.IO cliente y estado reactivo en frontend (chatStore) | HIGH | feat / integration | TODO | [ISSUE-CHAT-05] |
| #541 | Suite de pruebas unitarias, integración y Socket.IO del chat | HIGH | test / quality | TODO | [ISSUE-CHAT-06] |

---

## Feature Summary

### Infraestructura
- **#536 MongoDB (HIGH):** contenedor `tasker-db-mongo` (`mongo:7.0-alpine`), volumen `tasker-mongo-data`, env `TASKER_MONGO_URL` leída en `config/storage.py` con fallback seguro

### Backend
- **#537 Esquema y repositorio (HIGH):** `motor` asíncrono, colecciones `conversations`/`messages` con `user_id` inalterables del Auth Store (PostgreSQL), índices `conversation_id`/`participant_ids`/`created_at`
- **#538 Socket.IO servidor (CRITICAL):** `AsyncServer` + `socketio.ASGIApp` sobre FastAPI, handshake JWT (`auth['token']`, rechazo 401), salas por `conversation_id` con `enter_room`, eventos `join_room`/`leave_room`/`send_message`/`typing_start`/`typing_stop`/`mark_as_read` → `new_message`/`messages_read`, proxy nginx con upgrade
- **#539 REST (MEDIUM):** `/api/v1/chat/*` (conversaciones del usuario, creación con `participant_ids` reales, mensajes paginados, pin) con persistencia + `sio.emit('new_message', data, room=conversation_id)` desde `POST .../messages`

### Frontend
- **#540 Cliente Socket.IO (HIGH):** `socket.io-client` con `io(SOCKET_URL, { auth: { token } })` (JWT de `authStore`), unión/salida de salas, listeners reactivos en `ChatView`/`FloatingChat`, estado de conexión visual, `reconnect` + resync de mensajes perdidos, conmutación por `apiMode` (mock intacto)

### Calidad
- **#541 Tests (HIGH):** `pytest` + `pytest-asyncio` (autoría = `user_id` del JWT), TestClient de python-socketio (conexión + 2 clientes en la misma sala), repositorio con Mongo fake, vitest para `chatStore` (real/mock) y `ChatView`/`ChatInput` (tipeo + sanitización PII)

---

## Dependencies (suggested order)

1. **#536** (HIGH) — Mongo accesible antes de modelar; desbloquea #537
2. **#537** (HIGH) — repositorio que consumen #538 y #539
3. **#538** (CRITICAL) — servidor Socket.IO que notifica #539 y consume #540
4. **#539** (MEDIUM) — REST + emisión compartida con el servidor
5. **#540** (HIGH) — cliente frontend sobre #538/#539
6. **#541** (HIGH) — blindaje de #536–#540 (los tests pueden ir en paralelo por issue)

---

## Related Done Issues

| Done | Relevant to |
|---|---|
| #525, #533 | Compose/storage/health → #536 |
| #526, #527, #304 | user_id/Auth Store/infra → #537 |
| #519, #527, #472 | JWT y streaming → #538 |
| #517, #504, #522 | API real + streams → #539 |
| #517, #477, #504, #472 | realtime frontend/presencia → #540 |
| #518, #63 | Suite tests/CI → #541 |

---

## Release Checklist (backlog)

- [x] **#536** implemented — DONE 2026-10-01 (moved to `.issues/done/`, `features.md` §1 topología; imagen `mongo:7.0` por tag alpine inexistente)
- [x] **#537** implemented — DONE 2026-10-02 (moved to `.issues/done/`, `motor` en pyproject+requirements, 16 tests)
- [x] **#538** implemented — DONE 2026-10-02 (moved to `.issues/done/`, `python-socketio` + ASGIApp + nginx `/socket.io/`, smoke cliente real)
- [ ] **#539** implemented — move to `.issues/done/`, `features.md` (chat/REST)
- [ ] **#540** implemented — move to `.issues/done/`, `features.md` (chat/frontend)
- [ ] **#541** implemented — move to `.issues/done/`, `features.md` (chat/tests)
- [ ] Each issue: gates backend (`ruff`/`mypy`/`pytest`), `lint`/`test`/`build` si aplica UI, i18n EN+ES si aplica UI
- [ ] Move issue file to `.issues/done/` with `Status: DONE` when complete
- [ ] Commit message references `#NNN`
