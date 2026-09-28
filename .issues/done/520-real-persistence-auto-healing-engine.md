# Issue #520: Real Persistence & Auto-Healing Pipeline Engine

## Description

La vista *Auto-Healing Pipeline Monitor* (`AutoHealingMonitorView`) funciona con datos estáticos y simulados de ejecuciones (`autoHealingStore` con runs sembrados). Se debe conectar la interfaz con un ejecutor real de pipelines en el backend, permitir reinicio/cancelación en vivo de etapas y visualizar/descargar los parches `.patch` o diffs realmente aplicados al repositorio.

Origen: `notas.md` → [ISSUE-04] Persistencia Real y Motor del Pipeline de Auto-Healing (→ #520).

## Status: DONE

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
- [x] Pipeline monitor reads real execution runs from the backend (mock fallback preserved)
- [x] Restart or cancel of live pipeline stages from the UI
- [x] View and download the actual `.patch`/diff files applied to the repository
- [x] Stage progress updates live without page reload
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Verification (2026-09-27)

- Backend: `tests/api/test_auto_healing_unit.py` 7/7; `pytest -k "not integration"` 1016 passed / 3 pre-existing failures; `ruff` 1012 (≤ HEAD), `mypy` 1158/133 (HEAD 1173/133), delta no positivo.
- Frontend: `npm run lint` 0 errors, `npm test` 91/91, `npm run build` green.
- Docker (:19001): real run → 5/5 `completed`, commit `706cfab`, fix issue created in Neo4j, patch download 200 attachment with real unified diff; cancel → `cancelled` (2nd → 409); restart on cancelled → `completed` with a fresh patch; 404s and 409 conflict codes verified.

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
