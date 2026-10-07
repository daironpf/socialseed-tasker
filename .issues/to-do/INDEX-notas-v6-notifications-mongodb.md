# Notificaciones Reales en MongoDB Backlog — Issue Index

**Source:** `notas.md` (v6 — Épica: Sistema de Notificaciones Real en MongoDB, del modelo de datos y la API REST al stream en vivo y la integración del store)
**Created:** 2026-10-04
**Status:** DONE (5/5: #547, #548, #549, #550, #551) + follow-up DONE (#552, #553, #554, #555, #556, #557)

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
>   (Verificado al implementar #549: `_wipe_mongo` ya **no** usa lista fija —
>   dropea todas las colecciones no-`system.*` incluida `notifications`;
>   el AC queda cubierto y fijado con `test_wipe_mongo_drops_notifications_collection`.)
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
| #548 | API RESTful completa para notificaciones (`/api/v1/notifications`) | CRITICAL | feat / backend | DONE (2026-10-04) | Issue #2 |
| #549 | Notificación de bienvenida del sistema al instalar/iniciar | MEDIUM | feat / integration | DONE (2026-10-04) | Issue #3 |
| #550 | Eventos en tiempo real de notificaciones vía SSE (`/notifications/stream`) | HIGH | feat / realtime | DONE (2026-10-04) | Issue #4 |
| #551 | Integración del `notificationsStore` con la API real (`apiMode = real`) | HIGH | feat / integration | DONE (2026-10-05) | Issue #5 |
| #552 | Onboarding de primera entrada tras instalar (2 notificaciones + probe de modo real + auto-login) | HIGH | feat / integration | DONE (2026-10-06) | Issue #3 (extendido) |
| #553 | Detalle inline de notificaciones al hacer clic (panel + feed) | MEDIUM | feat / UX | DONE (2026-10-06) | follow-up de #551/#552 |
| #554 | Login con usuario y contraseña en el LoginScreen (modo credentials por defecto) | MEDIUM | feat / UX | DONE (2026-10-06) | follow-up de #552 |
| #555 | `tasker setup` reconstruye imágenes siempre (fix de despliegue obsoleto) | HIGH | bug fix / infra | DONE (2026-10-06) | follow-up de #542/#552 |
| #556 | Vista de Usuarios en modo real: normalización de la tarjeta + guard del último usuario | HIGH | bug fix / UX | DONE (2026-10-06) | follow-up de #519/#526 |
| #557 | Login en vista limpia (sin el proyecto visible detrás) | HIGH | bug fix / UX | DONE (2026-10-06) | follow-up de #554/#552 |

> **#552 (follow-up):** el bug de primera entrada tras instalar (5 HITL de la demo mock en
> lugar del onboarding) se diagnosticó como 3 causas encadenadas: default mock en navegador
> nuevo (sin `VITE_USE_MOCK` en los builds), guard de `/setup` saltado en mock, y bienvenida
> invisible por falta de sesión (`!!API_KEY` en `isAuthenticated` + sin auto-login). Amplía el
> Issue #3 de `notas.md` a **dos** notificaciones (bienvenida + "Define tus agentes en
> Usuarios"), añade el probe de `/health` al arrancar, auto-login tras el wizard y la master
> key como credenciales de LoginScreen. Fichero: `.issues/done/552-post-install-onboarding-first-entry.md`.

> **#553 (follow-up):** reportado al probar el flujo de #552 — hacer clic en una notificación
> no mostraba su detalle: el mensaje estaba truncado a 1 línea, el clic solo navegaba a
> `linkTo` (sin leerse nunca el texto) y el feed del board ni siquiera tenía handler de clic.
> Implementa expansión **inline** del mensaje completo (una fila abierta a la vez, marca leída,
> botón "Abrir" con `linkTo`) en `NotificationItem` (panel) y `NotificationsFeed` (board);
> HITL conserva su `HITLQuickActionModal`. Clave i18n `notifItem.open`. Fichero:
> `.issues/done/553-notificacion-detalle-inline.md`.

> **#554 (follow-up):** al desplegar #552/#553 el usuario reportó que el LoginScreen "pide
> la clave API" sin dejar introducir usuario/contraseña. El backend ya aceptaba
> `{username,password}` (#526, verificado en vivo con `admin/admin` → 200) y el frontend ya
> tenía `loginWithCredentials` (#552), pero la UI solo renderizaba el campo de API key.
> Implementa el modo **credentials por defecto** (usuario + clave → `loginWithCredentials`)
> con conmutador al modo API key (master key #552 intacta) y OAuth sin cambios; 6 claves
> `auth.*` EN/ES. Fichero: `.issues/done/554-login-usuario-clave-login-screen.md`.

> **#555 (follow-up):** causa raíz del despliegue obsoleto que enmascaró #552/#553 —
> `compose_up` solo pasaba `--build` con `--dev`, así que `tasker setup` normal horneaba
> (reutilizaba) imágenes viejas: `tasker-board` sirvió un bundle de días atrás pese a que
> el dist local ya estaba reconstruido. Ahora `docker compose up -d --build` es **siempre**
> (caché de Docker), `--dev` queda deprecado pero aceptado; test que fija el comportamiento.
> Fichero: `.issues/done/555-tasker-setup-rebuild-images.md`.

> **#556 (follow-up):** la tarjeta del `admin` en la vista de Usuarios aparecía "bloqueada" en
> modo real — `GET /users` no devuelve `type`/`avatar`/`skills`/`last_active` y la vista gatea
> los botones con `v-if="user.type === 'human'"` → sin botones, badge "IA", fecha inválida.
> Normalización en `usersApi` (patrón `mergeStudioAgents`) + roles ADMIN/VIEWER en `formatRole`
> + opción de rol dinámica en el modal. Guard del **último usuario** (humano, no total —
> `users.length` fallaría porque los agentes mantendrían la cuenta): disabled en frontend con
> `humans.length <= 1` y **409** en `DELETE /users` del backend. Fichero:
> `.issues/done/556-vista-usuarios-normalizacion-y-guard.md`.

> **#557 (follow-up):** sin sesión, el LoginScreen se mostraba como ventana flotante **encima**
> del shell completo — el guard deja navegar a `/board` sin sesión (`rolesAllowed(undefined) →
> true`) y el board se montaba con datos detrás del overlay. Ahora `App.vue` renderiza el login
> **en lugar del** shell (`RouterView` no monta → cero peticiones en background) con backdrop
> sólido (`bg-white dark:bg-gray-900`); tras login exitoso el reload pinta el board. Fichero:
> `.issues/done/557-login-vista-limpia.md`.

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
- **#551 Store real (HIGH):** nuevo `notificationsApi.ts`; `notificationsStore` ramificado por `isMockApi` (fetch + mutaciones a Mongo + suscripción `connectSSE('/notifications/stream')` con sonidos); categoría `welcome` + chip "System" + i18n EN/ES; preferencias `socialseed-alert-prefs` intactas en localStorage; specs vitest ampliados. Alcance ampliado: el `EventSource` no manda headers → fallback `?access_token=` en el stream (#550) + `SSEOptions.authenticate` en `realtime.ts` (token fresco por reconnect)

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
- [x] **#548** implemented — move to `.issues/done/` con `Status: DONE`, `features.md` §21 (§23 con #551)
- [x] **#549** implemented — move to `.issues/done/`, `features.md` §21/§69
- [x] **#550** implemented — move to `.issues/done/`, `features.md` §18/§21
- [x] **#551** implemented — move to `.issues/done/`, `features.md` §21/§22/§23
- [x] **#552** implemented (follow-up de #549/#551) — fichero en `.issues/done/`, `notas.md` Issue #3 ampliado, `features.md` §21/§62/§69
- [x] **#553** implemented (follow-up de #551/#552) — fichero en `.issues/done/`, `features.md` §57
- [x] **#554** implemented (follow-up de #552) — fichero en `.issues/done/`, `features.md` §64
- [x] **#555** implemented (follow-up de #542/#552) — fichero en `.issues/done/`, `features.md` §69
- [x] **#556** implemented (follow-up de #519/#526) — fichero en `.issues/done/`, `features.md` §11
- [x] **#557** implemented (follow-up de #554/#552) — fichero en `.issues/done/`, `features.md` §64
- [x] Each issue: gates backend (`ruff`/`mypy`/`pytest`), `lint`/`test`/`build` si aplica UI, i18n EN+ES si aplica UI
- [x] Move issue file to `.issues/done/` with `Status: DONE` when complete
- [ ] Commit message references `#NNN`
