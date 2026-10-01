# Issue #531: Checklists interactivas en la pestaña Progress

## Description

La pestaña Progress del `IssueDetailView` renderiza los logs de progreso como Markdown estático: `MarkdownRenderer` convierte `- [ ]`/`- [x]` en checkboxes **deshabilitados** (`disabled` en el HTML generado) y no hay persistencia del estado ni actualización en tiempo real. `notas.md` pide "listas de verificación interactivas (TODOs) actualizadas en tiempo real" dentro del modal de detalle del issue.

Origen: `notas.md` → ÉPICA 3 · Issue #8 (→ #531). El resto de la ÉPICA 3 (tab "AI Reasoning Logs" con Markdown, lista de archivos modificados, notas de deuda técnica) ya está done (#78, #210, #502, #469): esta issue cubre solo los TODOs interactivos.

## Status: DONE (2026-09-30)

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
- [x] Los TODOs del progress log se pueden marcar/desmarcar desde la UI
- [x] El estado del checklist persiste por issue tras recargar
- [x] Los cambios hechos por el agente u otros clientes se reflejan en tiempo real
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Files to Create
- `frontend/src/components/analysis/TaskChecklist.vue` (+ spec)
- `frontend/src/components/analysis/MarkdownRenderer.spec.ts`
- `frontend/src/utils/checklist.ts` (claves/parseo compartidos)

## Files to Modify
- `frontend/src/components/analysis/MarkdownRenderer.vue` — checkbox interactivo + emit (prop `interactive`)
- `frontend/src/views/IssueDetailView.vue` — handler de toggle + persistencia + suscripción
- `src/socialseed_tasker/infrastructure/web_api/routers/issues.py` + dominio — campo/endpoint de checklist (si la persistencia es server-side)
- `frontend/src/locales/en.json` / `es.json`
- `features.md` — §7

## Related Issues
- #78 (AI reasoning logs), #502 (Progress tab & tech debt), #469 (Rich text editor/Markdown), #530 (broadcast en tiempo real), #504 (mock SSE)

## Verification (2026-09-30)

**Contrato implementado (server-side):**
- Campo `task_checklist: dict[str, bool]` por issue; clave = texto del TODO normalizado (`trim` + colapso de espacios + minúsculas); solo se persisten overrides (el fallback es el marker `- [ ]`/`- [x]` del markdown).
- Backend: dominio `Issue.task_checklist`, `IssueUpdateRequest.task_checklist`, `IssueResponse.task_checklist`, mapeo en `convert_domain_issue_to_api_response`, lectura Neo4j en `_node_to_issue` (via `_json_obj`, acepta map nativo o JSON string como `update_issue` persiste dicts), mock server `IssueUpdate.task_checklist`.
- `PATCH /issues/{id}` con `task_checklist` emite `issue-updated` por SSE con `{issue_id, task_checklist}` (payload combinado con `agent_working` si vienen juntos; PATCH sin ninguno de los dos sigue sin broadcast).
- Frontend: `MarkdownRenderer` con props `interactive`/`checked` + emit `toggle` (delegación de `change`, `data-task-key` escapado); `TaskChecklist.vue` (contador ✓ `issues.checklistProgress` + re-emisión); `issuesStore.updateChecklist` (optimista + rollback + cola offline) y `applyIssueUpdate` mergea `task_checklist`; `IssueDetailView` usa `TaskChecklist` en los progress logs y lee el estado desde el store por id (propaga a las 3 vistas, incluida GraphView que guarda una copia local).

**Gates (baseline):**
- `ruff check src/` = 1011 (sin regresión), `mypy src/` = 1154/133 (sin regresión)
- `pytest -q` = 1166 passed / 27 skipped / 3 failed — solo los 3 preexistentes conocidos (`tests/events/test_delivery_retry.py::test_delivery_retries`, 2x `tests/workers/test_tasks_unit.py`); el 4º preexistente (`test_mock_server_start`, puerto 9010) pasó en esta ejecución
- `npm run lint` = 0 errores (2 warnings preexistentes vue/no-mutating-props en IssueDetailView), `npm test` = 203/203 (+15 nuevos: 7 MarkdownRenderer, 3 TaskChecklist, 5 issuesStore), `npm run build` verde
- Tests nuevos: `tests/api/test_issue_checklist.py` (7 tests: default, persistencia, reemplazo, broadcast, payload combinado, no-broadcast, 422)

**Smokes:**
- Real API/SSE (script contra :8888): 14/14 PASS — crea componente `Smoke Backend 531` + issue `Smoke 531 checklist` (id `a0e0ad4c-77d2-461f-91b1-5cc3d1ca9e04`); GET devuelve `task_checklist: {}`, PATCH persiste y relee desde Neo4j, valor inválido → 422, 2 clientes SSE reciben `issue-updated` con `task_checklist`, cleanup PATCH. Datos de smoke dejados en Neo4j (preferencia del usuario).
- Mock e2e Playwright (spec temporal borrada): 1/1 PASS — Kanban → issue `Implement OAuth2 with Keycloak` → tab Progress → contador visible → toggle de un TODO habilitado → recarga → el override persiste (server mock) → restauración del estado original.
- Board (:19001) sirve el bundle nuevo (`checklistProgress` presente en `assets/index-*.js`).

**Hallazgos / notas:**
- Neo4j perdió los datos previos (todos los contenedores `Exited (255)` ~1h antes, reinicio de Docker) — se recreó data de smoke; el gap de `project_id` documentado en #530 sigue abierto (IssueResponse sin `project_id` → Kanban real vacío), fuera de alcance aquí.
- Claves con caracteres especiales se persisten normalizadas en texto plano (round-trip `escapeHtml`/`unescapeHtml` verificado por test de XSS en `MarkdownRenderer.spec.ts`).
- Comportamiento asumido: TODOs con el mismo texto comparten estado (misma clave), documentado en el diseño.
