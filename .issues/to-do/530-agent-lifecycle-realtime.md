# Issue #530: Ciclo de vida `agent_working` en tiempo real

## Description

El icono de robot cian y el kill switch existen (#503, #59) y el backend expone `POST /issues/{id}/agent/start|finish|heartbeat|status` con validaciones 404/409, pero la UI alterna `agent_working` con un `PATCH /issues/{id}` genérico (no usa los endpoints dedicados; el kill switch envía `agent_working: false`) y no hay broadcast: el cambio no se refleja en tiempo real en otros clientes conectados (Kanban/Board). `notas.md` pide endpoints `/issues/{id}/start-agent` y `/issues/{id}/stop-agent` para alternar la bandera en tiempo real.

Origen: `notas.md` → ÉPICA 3 · Issue #7 (→ #530).

## Status: TODO

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
- [ ] Cuando `agent_working` es `true`, el icono de robot se renderiza en tarjetas Kanban, lista y detalle (comportamiento actual preservado)
- [ ] `POST /issues/{id}/start-agent` y `POST /issues/{id}/stop-agent` alternan la bandera (404/409 documentados)
- [ ] El cambio se propaga en tiempo real vía SSE a los demás clientes conectados
- [ ] i18n support (EN + ES); `npm run build` passes
- [ ] Gates backend sin regresiones

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
