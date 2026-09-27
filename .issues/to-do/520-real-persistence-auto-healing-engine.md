# Issue #520: Real Persistence & Auto-Healing Pipeline Engine

## Description

La vista *Auto-Healing Pipeline Monitor* (`AutoHealingMonitorView`) funciona con datos estáticos y simulados de ejecuciones (`autoHealingStore` con runs sembrados). Se debe conectar la interfaz con un ejecutor real de pipelines en el backend, permitir reinicio/cancelación en vivo de etapas y visualizar/descargar los parches `.patch` o diffs realmente aplicados al repositorio.

Origen: `notas.md` → [ISSUE-04] Persistencia Real y Motor del Pipeline de Auto-Healing (→ #520).

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Core / Auto-Healing / Pipelines

## Type
feat / core

## Implementation
1. **API del ejecutor:** nuevo `api/autoHealingApi.ts` contra endpoints reales (`/api/v1/auto-healing`: runs, stages, cancel, restart, patches) con polling o integración con el stream de #517; `autoHealingStore` con modo real y fallback mock (flag de #517).
2. **Control en vivo:** acciones *Cancel* y *Restart stage* en el detalle de run de `AutoHealingMonitorView` conectadas al backend; progreso de etapas actualizándose sin recargar la página.
3. **Parches reales:** `DiffViewer.vue` con botón de descarga del `.patch`/diff aplicado (contenido real del intento de fix, no sintético) y metadatos del commit/etapa que lo generó.
4. **Verificación** contra backend Docker con ejecuciones reales; el modo mock actual debe seguir funcionando sin backend (regresión).

## Acceptance Criteria
- [ ] Pipeline monitor reads real execution runs from the backend (mock fallback preserved)
- [ ] Restart or cancel of live pipeline stages from the UI
- [ ] View and download the actual `.patch`/diff files applied to the repository
- [ ] Stage progress updates live without page reload
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/api/autoHealingApi.ts`

## Files to Modify
- `frontend/src/stores/autoHealingStore.ts` — runs reales + acciones cancel/restart
- `frontend/src/views/AutoHealingMonitorView.vue` — controles en vivo
- `frontend/src/components/ui/DiffViewer.vue` — descarga de `.patch` real
- `frontend/src/locales/en.json` / `es.json` — pipeline actions
- `features.md` — cuando esté done

## Related Issues
- #86 (Automated Self-Healing), #494 (Auto-Healing Pipeline Monitor), #472 (Agent Streaming SSE/WebSocket), #514 (SLA & auto-healing analytics), #516 (Auto-healing success sound), #517 (Realtime architecture)
