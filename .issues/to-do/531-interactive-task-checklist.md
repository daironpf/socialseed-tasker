# Issue #531: Checklists interactivas en la pestaña Progress

## Description

La pestaña Progress del `IssueDetailView` renderiza los logs de progreso como Markdown estático: `MarkdownRenderer` convierte `- [ ]`/`- [x]` en checkboxes **deshabilitados** (`disabled` en el HTML generado) y no hay persistencia del estado ni actualización en tiempo real. `notas.md` pide "listas de verificación interactivas (TODOs) actualizadas en tiempo real" dentro del modal de detalle del issue.

Origen: `notas.md` → ÉPICA 3 · Issue #8 (→ #531). El resto de la ÉPICA 3 (tab "AI Reasoning Logs" con Markdown, lista de archivos modificados, notas de deuda técnica) ya está done (#78, #210, #502, #469): esta issue cubre solo los TODOs interactivos.

## Status: TODO

## Priority: LOW

## Component
Frontend / Issue Detail / UX

## Type
feat / ux

## Implementation
1. **Checkbox interactivo:** en `MarkdownRenderer` (o componente nuevo `TaskChecklist`), renderizar `- [ ]`/`- [x]` habilitados y emitir `toggle(item, checked)`; prop `interactive` (por defecto `false`) para no romper usos existentes (comentario de logs, docs).
2. **Persistencia:** guardar el estado por issue (campo `task_checklist` en la entidad/Neo4j o endpoint `POST /issues/{id}/checklist`), idempotente por item (clave = texto normalizado del TODO).
3. **Tiempo real:** combinar con el stream de agent logs / `issue-updated` (#530): cuando el agente añada o marque items, el checklist se re-renderiza sin recargar la vista.
4. **Feedback:** toggle optimista con rollback en error (toast) e i18n de estados.

## Acceptance Criteria
- [ ] Los TODOs del progress log se pueden marcar/desmarcar desde la UI
- [ ] El estado del checklist persiste por issue tras recargar
- [ ] Los cambios hechos por el agente u otros clientes se reflejan en tiempo real
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/components/analysis/TaskChecklist.vue` (+ spec)

## Files to Modify
- `frontend/src/components/analysis/MarkdownRenderer.vue` — checkbox interactivo + emit (prop `interactive`)
- `frontend/src/views/IssueDetailView.vue` — handler de toggle + persistencia + suscripción
- `src/socialseed_tasker/infrastructure/web_api/routers/issues.py` + dominio — campo/endpoint de checklist (si la persistencia es server-side)
- `frontend/src/locales/en.json` / `es.json`
- `features.md` — §7

## Related Issues
- #78 (AI reasoning logs), #502 (Progress tab & tech debt), #469 (Rich text editor/Markdown), #530 (broadcast en tiempo real), #504 (mock SSE)
