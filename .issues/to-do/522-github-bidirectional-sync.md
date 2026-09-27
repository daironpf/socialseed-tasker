# Issue #522: Bidirectional Real Sync with GitHub

## Description

El widget de sincronización con GitHub (`GitHubSyncCard`) simula los estados (SYNCED / PENDING_PUSH / ERROR). Se debe integrar la sincronización bidireccional real vía Webhooks de GitHub para actualizar el estado de issues, pull requests y comentarios, y manejar la resolución de conflictos cuando una issue se actualiza simultáneamente en GitHub y en Tasker.

Origen: `notas.md` → [ISSUE-06] Sincronización Bidireccional Real con GitHub (→ #522).

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Integration / GitHub / Sync

## Type
feat / integration

## Implementation
1. **API real de sync:** `api/githubSyncApi.ts` (estado de sincronización, force re-sync, eventos de webhook, vínculo issue↔PR) + store de sincronización; `GitHubSyncCard` muestra estado real (último sync, enlace a PR/issue, errores) con refresh y polling/stream según #517; se elimina la simulación local de estados.
2. **Webhooks bidireccionales:** el backend recibe webhooks de GitHub (issues, PRs, comments) y actualiza Tasker; la UI se suscribe a esos cambios (stream o polling) para reflejarlos en `IssueDetailView` sin recargar.
3. **Resolución de conflictos:** detectar doble edición (GitHub + Tasker simultáneos) y mostrar badge de conflicto en la issue; resolver en UI reutilizando el patrón de `SyncQueueDrawer` (Keep local / Keep remote / Merge) aplicado a issues sincronizadas.
4. **Acciones desde Tasker:** cambiar estado y comentar desde la UI reflejándose en GitHub (push bidireccional), con errores visibles; las acciones hechas offline se encolan con la cola de #515.
5. i18n + build + smoke con backend.

## Acceptance Criteria
- [ ] `GitHubSyncCard` shows the real sync state (no simulated SYNCED/PENDING_PUSH/ERROR)
- [ ] Webhook-driven, bidirectional updates for issues, pull requests and comments
- [ ] Conflict resolution UI when an issue changes in GitHub and Tasker simultaneously
- [ ] Actions made offline integrate with the #515 queue
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/api/githubSyncApi.ts`
- `frontend/src/components/sync/GitHubConflictResolver.vue` (o extensión de `SyncQueueDrawer`)

## Files to Modify
- `frontend/src/components/issue/GitHubSyncCard.vue` — estado real + acciones
- `frontend/src/stores/issuesStore.ts` — eventos entrantes de GitHub
- `frontend/src/views/IssueDetailView.vue` — badge/resolución de conflictos
- `frontend/src/components/sync/SyncQueueDrawer.vue` — conflictos GitHub
- `frontend/src/locales/en.json` / `es.json` — GitHub sync states
- `features.md` — cuando esté done

## Related Issues
- #88 (GitHub API Adapter), #89 (Bidirectional Webhook Listener), #93 (GitHub Issue Mapper), #95 (Webhook Signature Validator), #307 (Webhook Receiver & Event Bus), #500 (GitHub Sync Widget on Issue Detail), #515 (Offline Queue)
