# Issue #513: Mock Agent Simulator & Custom Agent Builder Studio

## Description

Para que las empresas puedan evaluar el potencial del sistema, deben poder simular la creación de nuevos agentes personalizados con roles específicos, herramientas asignadas y límites operativos, sobre el backend simulado actual.

Origen: `notas.md` → Issue #505 (renumerada a #513; #505 ya está en done como FilterBuilder).

## Status: DONE

**Resolución (2026-09-24):** Implementado. `AgentStudioView` en `/agents/studio` con builder (nombre, rol, avatar, modelo, system prompt con `AgentPromptEditor` + validación y variables insertables, 9 tools en checkbox, límites tokens/timeout/maxRisk), Sandbox Tester (`AgentSandboxTester`: chat mock determinista por herramientas/rol, action log escalonado, guardrail `maxRisk=LOW` que rechaza peticiones de alto riesgo) y Library (`AgentLibrary`: cards con modelo, estado, herramientas, límites, último uso, Editar/Clonar/Activar/Eliminar). Store `agentStudioStore` persiste en localStorage `agent-studio-v1` y sincroniza con `usersStore`; `usersApi.fetchUsers` mergea los agentes studio vía `utils/studioAgents.ts` (sobreviven al refetch y aparecen en UsersView y en los asignados de issues). Botón de acceso en UsersView, nav en Sidebar/MobileDrawer (grupo Management), i18n `agentStudio` + `nav.agentStudio` EN/ES. `users.json` y `server.py` intactos (persistencia mock vía localStorage, válida según AC). `npm run build` pasa (42s).

## Priority: MEDIUM

## Component
Frontend / Agents / Builder Studio

## Type
feat / agents

## Implementation
1. **Vista `AgentStudioView`:**
   - Nueva ruta `/agents/studio` (o `/agent-studio`)
   - Constructor visual: nombre, modelo base (GPT-4o, Claude 3.5 Sonnet, Llama 3, …), system prompt (`AgentPromptEditor`), herramientas permitidas (Tools/Capabilities checkboxes), límites operativos (max tokens/run, timeout, riesgo máximo)
   - Integrar con `usersStore` / agentes existentes (tipo `agent`)

2. **Sandbox Tester:**
   - Consola de pruebas dentro de la UI para interactuar con el agente recién creado
   - Chat simulado estilo `ChatInput` + respuestas mock deterministas por herramientas/rol
   - Log de "acciones" del agente (usa `useMockStream` o pasos estáticos)
   - Feedback de validación de prompt (mock: longitud, herramientas requeridas)

3. **Biblioteca corporativa de agentes:**
   - Guardar, clonar, activar/desactivar agentes en mock (`users.json` o `agents.json`)
   - Lista/biblioteca con cards: modelo, estado, herramientas, último uso
   - Persistencia mock API (`POST/PATCH/DELETE /mock/users` o endpoint agents dedicado)

4. **Tipos y store:**
   - `AgentProfile` en types; `agentStudioStore` o extender `usersStore`
   - Sincronizar con UsersView (agentes creados aparecen en asignación de issues)

## Acceptance Criteria
- [x] `AgentStudioView` builds agents with name, base model, system prompt, allowed tools/capabilities
- [x] Sandbox Tester lets user chat with the new agent on the simulated backend
- [x] Save, clone, enable/disable agents in corporate library (mock persistence)
- [x] New agents appear in UsersView and issue assignee dropdowns
- [x] Operative limits (tokens/run, risk) stored on agent profile
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Files to Create
- `frontend/src/views/AgentStudioView.vue`
- `frontend/src/components/agents/AgentPromptEditor.vue`
- `frontend/src/components/agents/AgentSandboxTester.vue`
- `frontend/src/components/agents/AgentLibrary.vue`
- `frontend/src/stores/agentStudioStore.ts`
- `frontend/src/types/agentStudio.ts`

## Files to Modify
- `frontend/src/router/index.ts` — `/agents/studio`
- `frontend/src/components/layout/Sidebar.vue` / `MobileDrawer.vue` — nav entry
- `frontend/src/stores/usersStore.ts` — library actions, clone/enable
- `frontend/src/views/UsersView.vue` — link to Studio / show studio-created agents
- `frontend/src/api/mockApi.ts` or `usersApi.ts` — agent create/clone if needed
- `frontend/dataset-de-pruebas/users.json` — seed studio agents optional
- `mock-api/server.py` — optional agents endpoints
- `frontend/src/locales/en.json` / `es.json` — agentStudio section
- `features.md` — when done

## Related Issues
- #487 (Agent Creation CreateUserModal), #474 (Agent Lifecycle Management), #488 (MCP Live Inspector), #11 (Users Management), #28 (Chat System)
