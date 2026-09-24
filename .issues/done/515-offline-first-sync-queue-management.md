# Issue #515: Offline First Capabilities & Mock Sync Queue Management

## Description

Garantizar que la interfaz sea rápida, tolerante a cortes de red y capaz de operar completamente fuera de línea, encolando acciones simuladas para cuando se restablezca la conexión. Complementa el indicador de red existente (#499) con cola real de mutaciones pendientes.

Origen: `notas.md` → Issue #507 (renumerada a #515; #507 ya está en done como HITL Quick Actions).

## Status: DONE

## Resolution
- **Simulador de red:** `NetworkModeToggle` segmentado (Online/Degraded/Offline) montado en `AppHeader`; `uiStore.networkMode` persistido en localStorage + `ConnectionState` ampliado con `DEGRADED`.
- **Cola offline:** `utils/offlineQueue.ts` (tipos, persistencia localStorage `socialseed-offline-queue`, `simulateRemoteVersion` con drift determinista de priority/status/is_active/title) + `uiStore` con `enqueueMutation`/`flushQueue`/`setNetworkMode`/`removeQueued`/`retryQueued`/`resolveConflict`; flush: OFFLINE_QUEUED -> SYNCING (400+900 ms) -> SYNCED conservando conflictos; cola restaurada y auto-flusheada al recargar; `simulateSync()` guardado para no pisar la cola.
- **Hooks:** `issuesStore.createIssue`/`updateIssue` y `policiesStore.createPolicy`/`updatePolicy` aplican localmente + encolan en modo offline (flag `skipOfflineQueue` para aplicar resoluciones); rama online intacta.
- **Drawer:** `SyncQueueDrawer` (overlay + panel) con lista, resumen, reintentos, borrado, resolucion de conflictos Keep local / Keep remote / Merge (textarea JSON) y boton Force sync; `SyncStatusBadge` ahora es boton que abre el drawer, muestra contador y estados DEGRADED/Offline.
- i18n: secciones `offline` + `syncQueue` (EN/ES, 70 secciones totales). `npm run build` pasa (42.74s).


## Priority: MEDIUM

## Component
Frontend / UX / Offline / Sync Queue

## Type
feat / ux

## Implementation
1. **Simulador de estado de red:**
   - Estados: Online / Degraded / Offline en toolbar de desarrollo o pie de página
   - Extender `uiStore.connectionState` o añadir `networkMode: 'online' | 'degraded' | 'offline'`
   - Control para forzar cada estado (demo/mock)

2. **Operación offline con cola:**
   - En modo Offline: permitir crear/editar issues y políticas
   - Encolar mutaciones en `pendingSyncCount` + estructura de cola persistida en **LocalStorage** (IndexedDB opcional/futuro)
   - Cada entrada: operación, payload, timestamp, entidad, reintento
   - Al volver a Online: flush simulado de la cola (transición OFFLINE_QUEUED → SYNCING → SYNCED existente)

3. **`SyncQueueDrawer`:**
   - Ventana emergente para inspeccionar la cola
   - Resolver conflictos simulados (ej. versión local vs. mock remoto: Keep local / Keep remote / Merge manual)
   - Botón "Forzar sincronización"
   - Contador sincronizado con `pendingSyncCount` y `SyncStatusBadge`

4. **Integración:**
   - Hook en `issuesStore` y `policiesStore` (create/update) para encolar si offline
   - No romper modo online actual ni mock API

## Acceptance Criteria
- [x] Network state simulator (Online / Degraded / Offline) in toolbar or footer
- [x] In Offline mode, create/edit issues and policies queue changes (LocalStorage + pendingSyncCount)
- [x] SyncQueueDrawer inspects queue, resolves simulated conflicts, and forces sync
- [x] Reconnect flushes queue and drives SyncStatusBadge through OFFLINE_QUEUED → SYNCING → SYNCED
- [x] Queue survives page reload
- [x] Online path unchanged for normal CRUD
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Files to Create
- `frontend/src/components/sync/SyncQueueDrawer.vue`
- `frontend/src/components/sync/NetworkModeToggle.vue`
- `frontend/src/utils/offlineQueue.ts` (or composable `useOfflineQueue.ts`)

## Files to Modify
- `frontend/src/stores/uiStore.ts` — networkMode, queue integration
- `frontend/src/stores/issuesStore.ts` — enqueue mutations when offline
- `frontend/src/stores/policiesStore.ts` — enqueue mutations when offline
- `frontend/src/components/ui/SyncStatusBadge.vue` — open drawer / mode display
- `frontend/src/components/layout/AppHeader.vue` or App shell — mount toggle/drawer
- `frontend/src/locales/en.json` / `es.json` — offline, syncQueue sections
- `features.md` — when done

## Related Issues
- #499 (Network Status & Sync Indicator), #91 (Offline-First Sync Engine backend), #94 (Connectivity Manager Sync Queue), #21 (Notifications), #5 (Issues List)
