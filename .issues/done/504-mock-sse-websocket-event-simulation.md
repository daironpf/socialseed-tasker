# Issue #504: Mock SSE/WebSocket Event Simulation Engine

## Description

El panel de logs del agente (`AgentLogStream`), los indicadores de typing (`TypingIndicator`) y las notificaciones en tiempo real dependen de eventos SSE. Actualmente son estáticos o dependen de triggers manuales. Debemos implementar un motor de simulación de presencia/eventos en tiempo real mediante un composable local (`useMockStream.ts`).

## Status: DONE

## Priority: HIGH

## Component
Frontend / Real-Time / Agent Simulation

## Implementation
1. **Crear Composable `useMockStream.ts`:**
   - Generar una cola de eventos programados (`setInterval`) que emita logs simulados del agente cuando un issue tenga `agent_working === true`
   - Tipos de eventos simulados: reasoning steps, file changes, code analysis, completion markers
   - Control de velocidad: `1x`, `2x`, `5x` selector
   - Auto-stop cuando el agente termina o es killed

2. **Interactividad con la UI:**
   - En `IssueDetailView.vue`, activar el streaming automático al abrir la pestaña "AI Reasoning"
   - Alternar estados de `TypingIndicator` y `PresenceAvatars` para simular que otros 2 usuarios/agentes están viendo/editando la misma tarea
   - Actualizar contadores de tokens en tiempo real

3. **Controles de Simulación:**
   - Añadir selector de velocidad (`1x`, `2x`, `5x`) en el encabezado del stream
   - Botón pause/resume para la simulación
   - Indicador visual de "live" vs "paused"

4. **Mock Data Generation:**
   - Script para generar logs realistas: reasoning steps, file modifications, dependency checks, test results
   - Distribución temporal realista (no todos los eventos de golpe)

## Acceptance Criteria
- [ ] `useMockStream.ts` composable created and functional
- [ ] Agent logs auto-stream when AI Reasoning tab is open
- [ ] TypingIndicator and PresenceAvatars toggle realistically
- [ ] Token counters update in real-time
- [ ] Speed selector (1x/2x/5x) works correctly
- [ ] Pause/resume controls work
- [ ] Simulation stops when agent is killed
- [ ] i18n support (EN + ES)

## Files to Create
- `frontend/src/composables/useMockStream.ts`

## Files to Modify
- `frontend/src/views/IssueDetailView.vue` — integrate mock stream in AI Reasoning tab
- `frontend/src/components/ui/AgentLogStream.vue` — add speed selector, pause controls
- `frontend/src/stores/uiStore.ts` — add simulation state
- `frontend/src/locales/en.json` — add mockStream section
- `frontend/src/locales/es.json` — add mockStream section

## Related Issues
- #472 (Agent Streaming SSE), #474 (Agent Lifecycle Management), #503 (Agent Timer & Kill Switch)
