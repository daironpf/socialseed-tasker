# Issue #551: Integración del `notificationsStore` con la API real (`apiMode = real`)

## Description

Refactorizar `src/stores/notificationsStore.ts` y la capa API (nuevo `src/api/notificationsApi.ts`) para que consuma los endpoints reales de MongoDB cuando `apiMode === 'real'`, escuchando el stream en vivo de #550 y preservando filtros y preferencias del usuario.

Contexto real del repo: hoy el store es 100% cliente — 12 fixtures (`seedMockNotifications`) persistidos en `localStorage`, acciones `addNotification`/`markAsRead`/`markAllAsRead`/`dismiss`/`markManyRead`/`dismissMany`/`getFiltered`/`ensureHitlNotifications` y preferencias de sonido en `socialseed-alert-prefs`; **no existe `notificationsApi.ts`**. `NotificationCategory` tiene 5 categorías fijas (`mention|hitl|constraint_violation|agent_failure|sla`) con `CATEGORY_CONFIG`, `SEVERITY_GROUPS` (Emergency/Warning/Info) y chips de canal en `NotificationCenter` — el `type`/`channel` `WELCOME`/`system` de #549 necesita categoría nueva + i18n. El patrón de ramificación por `isMockMode()` ya está probado en `ragStore`/`mcpStore`/`autoHealingStore` (#524/#520) y el cliente SSE en `api/realtime.ts:connectSSE` (#517); HITL/menciones siguen generándose en cliente (no hay workflow HITL en backend, §50 de `features.md`).

Origen: `notas.md` → Sistema de Notificaciones Real en MongoDB · Issue #5 (→ #551).

## Status: DONE (2026-10-05)

## Priority: HIGH

## Component
Frontend / Notifications / Stores

## Type
feat / integration

## Implementation
1. **`frontend/src/api/notificationsApi.ts`:** `fetchNotifications({read?, category?, limit?, offset?})`, `markAsRead(id)`, `markAllAsRead()`, `deleteNotification(id)`, `clearAll()` contra `/api/v1/notifications` con el envelope camelCase de #548.
2. **`notificationsStore.ts` en modo real:**
   * `fetchNotifications()`: si `!isMockApi`, consultar `GET /notifications` e hidratar la lista (mock intacto: fixtures + localStorage).
   * Mutaciones (`markAsRead`, `markAllAsRead`, `dismiss`, `dismissMany`, `clear-all`) persisten en Mongo en real y mantienen el comportamiento local en mock.
   * Suscripción al stream de #550 con `connectSSE('/notifications/stream')` → `addNotification()` en caliente disparando los efectos de sonido configurados (`useSoundEffects` / `playForCategory`); desconexión al volver a mock o perder la sesión (ciclo de vida como en `chatStore`, #540).
3. **Categoría de bienvenida:** ampliar `NotificationCategory` con `welcome`, `CATEGORY_CONFIG` (icono/tinte), `SEVERITY_GROUPS` (grupo Info), chip de canal "System" en `NotificationCenter` e i18n EN/ES (ASCII en ES) para que la notificación de #549 se muestre con identidad propia.
4. **Preferencias preservadas:** `socialseed-alert-prefs` (sonidos por canal) sigue en localStorage; documentar la división — notificaciones en Mongo, preferencias en cliente.
5. **Tests:** ampliar `notificationsStore.spec.ts` (hoy cubre mock): modo real con `client`/`connectSSE` mockeados (hidratación, mutaciones → API, evento del stream → `addNotification` + sonido) y smoke de `NotificationCenter`; `npm test` 100% verde.

## Acceptance Criteria
- [x] Al iniciar sesión tras instalar la app, la notificación de bienvenida generada en MongoDB aparece inmediatamente en el `NotificationCenter` del header
- [x] Marcar como leída desde la UI persiste el cambio de forma síncrona en MongoDB
- [x] Las notificaciones llegadas por stream se insertan en caliente con el sonido según preferencias
- [x] Filtros por grupo/canal y preferencias de sonido intactos en mock y real
- [x] La suite de Vitest (`npm test`) se mantiene al 100% en verde; `lint`/`build` sin regresiones

## Files to Create
- `frontend/src/api/notificationsApi.ts`

## Files to Modify
- `frontend/src/stores/notificationsStore.ts` — ramas real/mock, fetch, mutaciones y stream
- `frontend/src/stores/notificationsStore.spec.ts` — tests del modo real
- `frontend/src/types/notifications.ts` — categoría `welcome` + config/severity groups
- `frontend/src/components/ui/NotificationCenter.vue` — chip de canal System + bienvenida
- `frontend/src/locales/en.json` / `frontend/src/locales/es.json` — claves de la nueva categoría

## Related Issues
- #548 (endpoints que consume), #549 (bienvenida que debe aparecer), #550 (stream que escucha), #517 (`connectSSE` + `apiMode`), #516 (sonidos/grupos preferencias), #540 (ciclo de vida de socket en el store), #518 (gates de suite)

## Notes

DONE (2026-10-05) — implementación completa, gates verdes, commit pendiente de confirmación.

**Gap de autenticación SSE resuelto (alcance ampliado):** `EventSource` no puede enviar el header `Authorization` y no hay cookies en el frontend (JWT en memoria, #519), por lo que el stream de #550 respondía 401 en navegador. Se añadió:

- Backend `notifications.py`: `_stream_user()` — fallback `?access_token=` verificado con el mismo `verify_access` del bearer header, usado solo por `stream_notifications` (REST sigue header-only). Tests nuevos: `test_stream_accepts_access_token_query_param`, `test_stream_rejects_invalid_query_token` (`_scope` ahora acepta `query`).
- Frontend `api/realtime.ts`: `SSEOptions.authenticate` — el token se lee en cada `open()` para que los reconnects nunca reutilicen un JWT vencido.

**Cambios adicionales necesarios** (fuera de la lista `Files to Modify` original):

- `frontend/src/components/dashboard/NotificationsFeed.vue` — `CATEGORY_STYLES` exige la nueva categoría (`Record<NotificationCategory, ...>`).
- `frontend/src/types/notifications.ts` — `linkTo` ahora acepta `{ path }` además de `{ name, params }`: el servidor manda `/users` y `router.push` acepta ambas formas (solo se leía en `NotificationItem`).
- Locales: además de `notifPanel.channel.welcome` ("System"/"Sistema") se añadieron `constraint_violation` y `agent_failure`, claves que los chips ya usaban sin traducción (hueco preexistente; `governance`/`agent` se mantienen por si acaso).

**Decisiones de diseño del store:**

- Arranque: en real solo si hay sesión (`authStore.user` — el router guard `beforeEach` ya awaits `initSession`, #519, antes de montar el header); watchers sobre `authStore.user` y `apiMode` con el patrón de `chatStore` (#540). `startRealtime()` es idempotente (`sseHandle` como guard) porque ambos watchers pueden dispararse en el mismo flush.
- `hydrate()` fusiona snapshot/servidor con los items locales `notif-` (HITL se sigue generando en cliente, §50) ordenado por `createdAt` desc; `notification_created` inserta con dedupe por `id` + sonido vía `preferences.channels` (mismo camino que `addNotification`).
- `persist()` y `loadFromStorage()` solo en mock: en real la historia vive en Mongo y no se filtra entre usuarios por `localStorage`.
- Mutaciones en real: optimistas + llamada API en fire-and-forget (`void ...catch`); solo ids de servidor (los `notif-` locales no existen en backend y darían 404). `markManyRead` delega en `markAsRead` por id; `dismissMany` hace DELETE por id de servidor.
- Logout: `stopStream()` + lista limpia (los datos del usuario anterior no quedan en memoria). Mock↔real: al volver a mock se limpia y reseedan fixtures.

**Gates:** backend `ruff src` 1011 (baseline), `mypy src` 1153 (baseline), `pytest` **1325 passed** (+2 nuevos), 3 failed preexistentes, 27 skipped. Frontend `npm run lint` 0 errores (2 warnings preexistentes en `IssueDetailView.vue`), `npm test` **282 passed / 40 files** (+11 store real-mode + 1 smoke `NotificationCenter`), `npm run build` OK, paridad i18n en/es 1683/1683 claves.
