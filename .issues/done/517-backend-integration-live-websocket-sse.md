# Issue #517: Backend Integration & Live WebSocket/SSE Architecture

## Description

La UI opera en modo de prueba (`USE_MOCK = true` en `frontend/src/api/client.ts:6`). Se debe integrar el cliente de la aplicación con los endpoints reales de FastAPI (`/api/v1`) y sustituir la simulación por conexiones WebSockets/SSE reales para el *Agent Log Streaming* y la presencialidad en tiempo real.

Origen: `notas.md` → [ISSUE-01] Backend Integration & Live WebSocket/SSE Architecture (→ #517).

## Status: DONE

## Priority: CRITICAL

## Component
Frontend / Architecture / Realtime / API

## Type
feat / architecture

## Implementation
1. **Modo real configurable:** flag `VITE_USE_MOCK` (env/build) + interruptor persistido en `uiStore` para alternar mock/real sin recompilar; `client.ts` expone el cliente elegido y mantiene `mockApi.ts` como fallback por endpoint.
2. **Llamadas reales:** reemplazar las lecturas JSON de `mockApi` por los módulos API existentes (`issuesApi`, `policiesApi`, `analysisApi`, `agentLogsApi`, `systemApi`, `usersApi`, `organizationsApi`, `constraintsApi`, `componentsApi`) con manejo de errores estandarizado; verificar paridad de shape mock↔real y añadir transformadores donde falte.
3. **Streaming en vivo:** sustituir `useMockStream` por transporte real (SSE `EventSource` / `WebSocket`) en `useAgentStream` y `usePresence`: canales de logs de agentes y presencialidad; reconexión con backoff exponencial + jitter, heartbeat y cierre limpio al logout.
4. **Estado visible:** `SyncStatusBadge` muestra el estado del stream (LIVE / RECONNECTING / OFFLINE) integrado con `networkMode` de #515; `frontend/nginx.conf` desactiva buffering en rutas SSE del bloque `location /api/`.
5. **Verificación:** `npm run build` verde; smoke contra backend Docker (`tasker-api` :8888) con modo real y con mock (regresión).

## Acceptance Criteria
- [x] API calls hit FastAPI `/api/v1` instead of JSON reads (mock still toggleable as fallback) — en modo Real todo `client` despacha a `realClient`/axios → `/api/v1`; paridad de shape por endpoint pendiente (ver `features.md` §50)
- [x] Agent Log Streaming and presence run over real SSE/WebSocket (no `useMockStream` en modo Real) — SSE en `api/realtime.ts`; el modo mock conserva `useMockStream` como fallback
- [x] Automatic reconnection with exponential backoff; stream state surfaced in `SyncStatusBadge` — backoff+jitter (max 8), watchdog 45s, estados Live/Connecting/Reconnecting/Stream offline + chip de fuente (Mock/Live)
- [x] Offline/degraded behavior from #515 preserved; mock mode regression-free — `networkMode` intacto; mock es el default; smoke Docker: mock-api y bundle sin cambios funcionales
- [x] i18n support (EN + ES) — `sync.*` + `apiMode.*`
- [x] `npm run build` passes

## Files to Create
- `frontend/src/api/realtime.ts` — cliente SSE/WS con backoff y heartbeat
- `frontend/.env.example` — documentar `VITE_USE_MOCK` y endpoints

## Files to Modify
- `frontend/src/api/client.ts` — flag real/mock configurable
- `frontend/src/api/mockApi.ts` — fallback por endpoint
- `frontend/src/composables/useAgentStream.ts` / `usePresence.ts` — transporte real
- `frontend/src/composables/useMockStream.ts` — aislar/retirar del flujo real
- `frontend/src/components/ui/SyncStatusBadge.vue` — estados del stream
- `frontend/src/stores/uiStore.ts` — preferencia mock/real persistida
- `frontend/nginx.conf` — `proxy_buffering off` + headers SSE en `/api/`
- `frontend/src/locales/en.json` / `es.json` — estados de conexión
- `features.md` — cuando esté done

## Related Issues
- #472 (Agent Streaming SSE/WebSocket), #504 (Mock SSE/WebSocket Event Simulation), #499 (Network Status & Sync Banner), #515 (Offline First & Sync Queue), #173 (Frontend Not Connecting to API)

## Resolution (2026-09-26)

Implementado sin WebSocket (SSE cubre los dos casos de uso: agent-logs y presencia):

- **Toggle mock/real:** estado `apiMode` en `client.ts` (orden: `localStorage` > `VITE_USE_MOCK` > `mock`), wrapper reactivo que despacha a `mockClient` (in-bundle) o `realClient` (axios → `/api/v1`); selector Mock/Real en `UserMenu` (`data-testid="api-mode-mock|real"`); facade en `uiStore`; `authStore`/`LoginScreen`/`pendingFeatures` con `isMockMode()`.
- **Cliente SSE:** `frontend/src/api/realtime.ts` — `connectSSE` con backoff exponencial+jitter (max 8 intentos), watchdog de 45s, estado agregado `realtimeState` (live/connecting/reconnecting/offline/idle).
- **Backend:** `web_api/routers/realtime.py` — `RealtimeHub` (ring buffer 200 logs, presencia TTL 90s, pub/sub asyncio); endpoints `GET/POST /issues/{id}/agent-logs`, `.../agent-logs/stream`, `GET/POST /issues/{id}/presence`, `POST .../presence/leave`, `GET .../presence/stream`; registrado en `routers/__init__.py`, `routes.py`, `app.py` (`app.state.realtime_hub`).
- **Protocolo:** `event: connected` + replay atómicos antes de suscribir a live, `event: log`/`event: viewers` en vivo, `event: ping` (evento nombrado, no comment) cada 15s; dedupe de logs por `id`/`timestamp|content_markdown`.
- **UI:** `useAgentStream`/`usePresence` con transporte real (watch `apiMode`), `SyncStatusBadge` con estados de stream + chip de fuente, `IssueDetailView` conecta al mount y por `issue.id` y mezcla REST+SSE en `displayLogs`; `mockStream.start()` solo en mock.
- **Infra:** `nginx.conf` con `proxy_buffering off`/`X-Accel-Buffering no`/`read_timeout 3600s` en `/api/`; `.env.example` documenta `VITE_USE_MOCK`/`VITE_API_URL`; i18n `sync.*`+`apiMode.*` EN/ES.
- **Verificación:** `npm run build` verde; `ruff check realtime.py` limpio (findings de `app.py` preexistentes en HEAD); Docker rebuild de `tasker-api`+`tasker-board` con smoke en `:19001`: SSE connected+replay, entrega en vivo, ping a 15s, presencia join/list/stream/leave, mock-api `:8001` intacto, UI sirve `index-BSCi2qGL.js`.
- **Doc:** `features.md` §62 nueva + gaps §50 actualizados.
- **Seguimiento:** paridad de shape de todos los endpoints REST en modo Real queda como gap (`features.md` §50).
