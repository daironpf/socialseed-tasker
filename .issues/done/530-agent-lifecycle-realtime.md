# Issue #530: Ciclo de vida `agent_working` en tiempo real

## Description

El icono de robot cian y el kill switch existen (#503, #59) y el backend expone `POST /issues/{id}/agent/start|finish|heartbeat|status` con validaciones 404/409, pero la UI alterna `agent_working` con un `PATCH /issues/{id}` genérico (no usa los endpoints dedicados; el kill switch envía `agent_working: false`) y no hay broadcast: el cambio no se refleja en tiempo real en otros clientes conectados (Kanban/Board). `notas.md` pide endpoints `/issues/{id}/start-agent` y `/issues/{id}/stop-agent` para alternar la bandera en tiempo real.

Origen: `notas.md` → ÉPICA 3 · Issue #7 (→ #530).

## Status: DONE (2026-09-30)

## Priority: MEDIUM

## Component
Backend + Frontend / Agents / Realtime

## Type
feat / observability

## Implementation
1. **Endpoints dedicados:** alias `POST /issues/{id}/start-agent` y `POST /issues/{id}/stop-agent` sobre la lógica existente de `agent/start`/`agent/finish`; `stop-agent` admite parada "humana" (kill switch) con `agent_id` opcional (hoy es obligatorio en `AgentFinishRequest`).
2. **Broadcast SSE:** emitir evento `issue-updated` (campos `agent_working`, `agent_working_started_at`) desde el hub de `realtime.py` cuando start/stop/PATCH cambien la bandera; stream `GET /issues/stream` (o canal por tablero) con el patrón `connected` + `ping` de #517.
3. **Frontend en vivo:** `IssueCard.killAgent` y `governanceStore` usan los endpoints dedicados; Board/Kanban/`IssueDetailView` se suscriben al stream y aplican el cambio sin recargar.
4. **Icono + temporizador:** verificar `AgentWorkingIcon` en Kanban, lista y detalle con el estado llegado por SSE.

## Acceptance Criteria
- [x] Cuando `agent_working` es `true`, el icono de robot se renderiza en tarjetas Kanban, lista y detalle (comportamiento actual preservado)
- [x] `POST /issues/{id}/start-agent` y `POST /issues/{id}/stop-agent` alternan la bandera (404/409 documentados)
- [x] El cambio se propaga en tiempo real vía SSE a los demás clientes conectados
- [x] i18n support (EN + ES); `npm run build` passes
- [x] Gates backend sin regresiones

## Verification (2026-09-30)

**Implementado:**
- Backend: `AgentToggleRequest` + `IssueResponse.agent_working_started_at`; ruta `GET /issues/stream` (antes de `/issues/{issue_id}`); hub `_issue_subs` + `publish_issue_update` en `realtime.py`; aliases `POST /issues/{id}/start-agent|stop-agent` (body opcional, `agent_id` default `"manual"`); emisión `issue-updated` en start/finish/PATCH; `POST /issues/{id}/agent/finish` acepta body vacío (kill humano).
- Frontend: `issuesApi.startAgent/stopAgent`; dispatch mock en `client.ts` (POST→`mockApi.updateIssue`); `issuesStore.startAgent/stopAgent` + suscripción `connectSSE('/issues/stream')` solo en modo real (`applyIssueUpdate` merge parcial); `IssueCard.killAgent` → `stopAgent` + toast `agent.agentStopped`; `governanceStore` (3 sitios) a endpoints dedicados; `mock-api` `IssueUpdate.agent_working_started_at`.

**Gates backend:** `ruff check src/` = 1011 (baseline) · `mypy src/` = 1154/133 (baseline) · `pytest -q` = 1158 passed / 27 skipped / 4 failed. 3 fallos preexistentes (`test_delivery_retry`, 2x `test_tasks_unit`); el 4º (`test_mock_server_start`) es ambiental: el puerto 9010 lo ocupa un proceso externo (Battle.net Agent, socket ESTABLISHED 127.0.0.1:9010) y `socket.bind('0.0.0.0', 9010)` reproduce el fallo sin tocar el repo — sin relación con #530 (`tools/contracts` no modificado).

**Gates frontend:** `npm run lint` 0 errores (2 warnings preexistentes `IssueDetailView.vue`) · `npm test` 188/188 (+5 de #530) · `npm run build` verde.

**Smoke real (API + SSE, :8888):** 2 clientes SSE conectados reciben `issue-updated` (8 eventos: start, stop, legacy start/finish, PATCH on/off); start/stop-agent 200 alternando la bandera; 409 en segundo start y en stop en reposo; 404 para id inexistente; legacy `agent/start|finish` 200; PATCH `agent_working` también emite; `GET /issues/stream` → 200 `text/event-stream` (no sombreado por `/issues/{issue_id}`); respuesta incluye `agent_working_started_at`.

**Smoke e2e (Playwright, tasker-board :19001):** mock — icono + temporizador en tarjeta Kanban con `agent_working`, kill switch habilitado → click → desaparece, 0 pageerrors. real (sesión `pedro`, refresh token inyectado) — tablero renderiza, icono aparece SIN recargar vía SSE tras `start-agent`, kill switch → desaparece y backend queda en `agent_working=false`, 0 pageerrors. (El harness inyectó `project_id` en las respuestas del listado; ver hallazgo.)

**Hallazgo fuera de alcance:** `IssueResponse` no incluye `project_id` (el dominio `Issue` tampoco lo tiene), por lo que `issuesStore.filteredIssues` descarta todos los issues reales y el Kanban real aparece vacío ("No issues in this project"). Preexistente a #530; sugiere issue aparte (backend: poblar `project_id` desde la relación con Project/Component o la propiedad `i.project`).

## Files to Create
- `tests/api/test_agent_lifecycle_stream.py`
- spec de frontend del stream/kill switch (extender `IssueCard.spec.ts`)

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/issues.py` — aliases `start-agent`/`stop-agent` + emisión
- `src/socialseed_tasker/infrastructure/web_api/routers/realtime.py` — canal `issues` + broadcast
- `frontend/src/components/issue/IssueCard.vue`, `frontend/src/stores/governanceStore.ts`, `frontend/src/stores/issuesStore.ts` — endpoints dedicados + suscripción
- `frontend/src/locales/en.json` / `es.json`
- `features.md` — §18/§43

## Related Issues
- #81 (Agent lifecycle integration), #474 (Agent lifecycle management), #503 (Kill switch), #59 (Robot indicator), #504/#517 (SSE architecture)
