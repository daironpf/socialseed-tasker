# Notificaciones Reales en MongoDB Backlog — Issue Index

**Source:** `notas.md` (v6 — Épica: Sistema de Notificaciones Real en MongoDB, del modelo de datos y la API REST al stream en vivo y la integración del store)
**Created:** 2026-10-04
**Status:** IN PROGRESS (1/5 done: #547; pendientes: #548, #549, #550, #551)

> `notas.md` (v6) define las issues como [Issue #1]…[Issue #5]; interpretando la carpeta
> `.issues/done/` el siguiente número libre era **#547** (máximo actual **#546**, cerrado en
> el backlog v5 de onboarding #542–#546), por lo que se numeraron **#547–#551** conservando
> el orden y contenido del plan original. Al igual que en el backlog v5, cada issue
> incorpora sus propios AC de gates (`ruff`/`mypy`/`pytest` y `lint`/`test`/`build` si aplica
> UI) en lugar de llevar una issue de tests propia. Los ficheros de issue viven en
> `.issues/to-do/` hasta que se implementan (se mueven a `.issues/done/` con `Status: DONE`).
>
> **Grounding contra el código real:**
> - No existe ni el paquete `src/socialseed_tasker/models/` ni rastro de
>   `/api/v1/notifications` ni de `notificationsApi.ts` (todo verde) — #547/#548 lo crean
>   desde cero; `notas.md` pide `models/notification.py` pese a que la convención del repo
>   (#537) dejó el schema Mongo en `infrastructure/mongo/`.
> - MongoDB ya está cableado por el chat: `config/storage.py:get_mongo_url()` lee
>   `TASKER_MONGO_URL` y `infrastructure/mongo/client.py:get_chat_database()` devuelve la
>   base `tasker` — #547 la reutiliza sin nueva env ni contenedor.
> - Patrón de repo Mongo con degradación tipada (`ChatStoreError`) en
>   `infrastructure/mongo/chat_repository.py` (#537) → réplica `NotificationStoreError`.
> - Identidad por JWT ya resuelta en `routers/chat.py` (`_current_user` →
>   `load_auth_provider().verify_token`, #527) y contrato `APIResponse` camelCase (#539)
>   → #548 no inventa nada nuevo.
> - `setup_initialize` (#543) wipea las colecciones Mongo del chat pero **no** `notifications`
>   → #549 debe ampliar el wipe para cumplir su AC de "exactamente una bienvenida".
> - Dos transportes probados: `RealtimeHub` SSE (#517, plantillas `/issues/stream` #530,
>   `/github-sync/stream` #522, `/mcp/tool-calls/stream` #524 con `ping` 15s y nginx
>   `proxy_buffering off`) y Socket.IO (#538); `notas.md` admite ambos → se recomienda SSE
>   (#550) por no tocar el servidor de salas del chat y poder testear el handler directo
>   (`TestClient.stream` cuelga en este entorno, lección de #524).
> - El store es hoy 100% localStorage (12 fixtures, `socialseed-alert-prefs`) con 5
>   categorías fijas en `types/notifications.ts` → #551 añade `welcome`, ramifica por
>   `isMockMode()` (patrón `ragStore`/`mcpStore` #524) y suscribe el stream.

---

## Issue Index

| # | Issue | Priority | Type | Status | notas.md |
|---|---|---|---|---|---|
| #547 | Modelo de datos MongoDB e infraestructura ODM para notificaciones | HIGH | feat / backend | DONE (2026-10-04) | Issue #1 |
| #548 | API RESTful completa para notificaciones (`/api/v1/notifications`) | CRITICAL | feat / backend | TODO | Issue #2 |
| #549 | Notificación de bienvenida del sistema al instalar/iniciar | MEDIUM | feat / integration | TODO | Issue #3 |
| #550 | Eventos en tiempo real de notificaciones vía SSE (`/notifications/stream`) | HIGH | feat / realtime | TODO | Issue #4 |
| #551 | Integración del `notificationsStore` con la API real (`apiMode = real`) | HIGH | feat / integration | TODO | Issue #5 |

---

## Feature Summary

### Backend / Datos
- **#547 Modelo Mongo (HIGH):** `src/socialseed_tasker/models/notification.py` con `id` (PyObjectId), `user_id`, `type` (`MENTION`/`HITL`/`CONSTRAINT_VIOLATION`/`AGENT_FAILURE`/`SLA`/`WELCOME`), `severity`, `title`, `message`, `read`, `requires_action`, `link_to`, `hitl_request_id`, `channel`, `created_at`; índices `{user_id, read}` y `{created_at}` idempotentes; acceso sobre `get_chat_database()` con `NotificationStoreError` degradada

### Backend / API
- **#548 REST (CRITICAL):** router `notifications.py` con `GET /notifications` (`read`/`category`/`limit`/`offset`, orden `created_at` desc), `PATCH /{id}/read`, `POST /mark-all-read`, `DELETE /{id}`, `POST /clear-all`; `user_id` siempre del JWT (aislamiento estricto), envelope `APIResponse` camelCase, tests con repo fake

### Backend / Onboarding
- **#549 Bienvenida (MEDIUM):** tras `POST /setup/initialize` inserta para el admin la notificación `WELCOME`/`INFO`/`channel=system` (`requires_action`, `link_to: "/users"`) con el payload literal de `notas.md`; wipe de Mongo ampliado con `notifications` para reinstalaciones; degradación sin Mongo; idempotencia

### Backend / Realtime
- **#550 SSE (HIGH):** `GET /api/v1/notifications/stream` con `connected` + snapshot, `notification_created` dirigido por usuario y `ping` 15s; fan-out por `user_id` (JWT) sobre el patrón `RealtimeHub`; limpieza de suscriptores y tests invocando el handler directo

### Frontend
- **#551 Store real (HIGH):** nuevo `notificationsApi.ts`; `notificationsStore` ramificado por `isMockApi` (fetch + mutaciones a Mongo + suscripción `connectSSE('/notifications/stream')` con sonidos); categoría `welcome` + chip "System" + i18n EN/ES; preferencias `socialseed-alert-prefs` intactas en localStorage; specs vitest ampliados

---

## Dependencies (suggested order)

1. **#547** (HIGH) — modelo/repo base; desbloquea #548 → #549 y #550
2. **#548** (CRITICAL) — contrato REST que consumen #549 (AC de primer login), #550 (emisiones) y #551
3. **#549** (MEDIUM) — primer emisor real; requiere #547 + wipe de #543
4. **#550** (HIGH) — stream en vivo; requiere #547/#548 (punto de inserción)
5. **#551** (HIGH) — integración UI sobre #548 + #550 (la parte REST puede avanzar antes que el stream)

---

## Related Done Issues

| Done | Relevant to |
|---|---|
| #536, #525, #537 | Mongo (`TASKER_MONGO_URL`, repo/errores) → #547 |
| #539, #543, #527, #520 | Router `APIResponse`/JWT/patrones de test → #548 |
| #543, #545, #546, #542 | Setup initialize/wipe/wizard → #549 |
| #517, #530, #522, #524, #538 | `RealtimeHub`/SSE/streams (y alternativa Socket.IO) → #550 |
| #516, #517, #540, #541, #518 | Sonidos, `apiMode`, ciclo de vida en store, suites → #551 |

---

## Release Checklist (backlog)

- [x] **#547** implemented — move to `.issues/done/` con `Status: DONE`, `features.md` §21
- [ ] **#548** implemented — move to `.issues/done/`, `features.md` §21/§23
- [ ] **#549** implemented — move to `.issues/done/`, `features.md` §21/§69
- [ ] **#550** implemented — move to `.issues/done/`, `features.md` §18/§21
- [ ] **#551** implemented — move to `.issues/done/`, `features.md` §21/§22/§23
- [ ] Each issue: gates backend (`ruff`/`mypy`/`pytest`), `lint`/`test`/`build` si aplica UI, i18n EN+ES si aplica UI
- [ ] Move issue file to `.issues/done/` with `Status: DONE` when complete
- [ ] Commit message references `#NNN`
