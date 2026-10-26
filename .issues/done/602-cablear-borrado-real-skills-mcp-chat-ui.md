# Issue #602: Cablear el borrado real (skills, mcp/servers, chat/conversations) en la UI + i18n EN/ES

## Description

Follow-up **explícito de #596** (cerrada como backend-only: *"los stores no tienen
funciones de delete; cableado de bots queda como follow-up"*). Los tres `DELETE`
existen y fueron verificados en vivo (verify 24/24 de #596), pero la **UI no puede
borrar nada en modo real**:

**Estado verificado (2026-10-26):**

- `frontend/src/stores/*.ts`: **0 funciones de delete** para skills/mcp/conversaciones
  (`chatStore`, `mcpStore`, store de skills — grep de `delete*`/`remove*` → nada).
- `ChatView.vue` y `MCPInspectorView.vue`: **0 handlers de borrado** (grep
  `delete|borrar|eliminar` → nada).
- `AgentSkillsView.vue:337` sí borra en real, pero es `deleteAgentSkill` — la
  **asignación** de skill (#577, `DELETE /users/{id}/skills/{skill_id}`), **no** el
  catálogo de #596.
- La UI de catálogo/MCP/chat no tiene botón cableado a la API → el usuario no puede
  dar de baja lo que la API ya permite borrar.

**Backend de referencia (ya listo, #596):**

| Endpoint | Respuesta éxito | Errores |
|---|---|---|
| `DELETE /api/v1/skills/{skill_id}` | 200 `{deleted, assignmentsRemoved}` | 404 / 503 sin PG |
| `DELETE /api/v1/mcp/servers/{server_id}` | 200 `{id, sessionsRemoved}` | 404 / 503 sin backend |
| `DELETE /api/v1/chat/conversations/{id}` | 200 (solo dueño JWT) | ajeno/inexistente → 404, Mongo caído → 503 |

## Status: DONE

## Priority: MEDIUM

## Component
Frontend (stores + vistas de Skills/MCP/Chat) + i18n

## Type
feat / frontend

## Implementation

1. **Stores** (patrón `isMockMode()` de #576/#577 — mock muta local, real llama API):
   - `mcpStore`: `removeServer(id)` → `DELETE /mcp/servers/{id}` + refetch de servers
     y sessions; mostrar `sessionsRemoved` en el feedback.
   - `chatStore`: `deleteConversation(id)` → `DELETE /chat/conversations/{id}` +
     quitar de la lista; si la conversación activa es la borrada, seleccionar otra o
     cerrar el panel.
   - Skills: localizar dónde vive el **catálogo** en la UI (vista de skills o
     `AgentSkillsView` si lista el catálogo) y añadir `deleteSkill(id)` — **cuidado
     con no confundir** con el `deleteAgentSkill` existente (asignación #577 ≠
     catálogo #596).
2. **Vistas**: botón de borrado con **diálogo de confirmación** (patrón de los
   confirm existentes: `agentSkills.delete`/`confirmDelete`), estado loading/disabled,
   feedback con los campos que devuelve el backend (`assignmentsRemoved`,
   `sessionsRemoved`) y manejo de errores: 404 → "no existe" (refetch), 503 →
   "backend no disponible" (mensaje degradado, patrón de #564).
3. **i18n EN/ES**: claves nuevas (o reutilización de las existentes de otros
   recursos: `delete`, `confirmDelete`, `deleted`, `deleteError`) en
   `frontend/src/locales/en.json` y `es.json` con **paridad total** — un test/grep de
   claves faltantes si el repo ya tiene el patrón.
4. **Tests**: spec por store (real: spy del cliente API con aserción de la URL
   DELETE; mock: mutación local) + specs de los handlers de vista donde aplique
   (patrón `*.spec.ts` existentes).

## Acceptance Criteria
- [ ] Skills (catálogo): borrado desde la UI en modo real → desaparece del listado;
      feedback con `assignmentsRemoved`; 404/503 manejados
- [ ] MCP: borrar server → sale de la lista y de `GET /mcp/sessions`
      (`sessionsRemoved` mostrado)
- [ ] Chat: borrar conversación → sale del listado; ajeno/inexistente → 404
      manejado; Mongo caído → 503 degradado; la activa se cierra/selecciona otra
- [ ] Confirmación previa en los 3 borrados (sin borrados accidentales)
- [ ] i18n EN + ES con paridad (0 claves faltantes)
- [ ] Gates frontend: vitest ≥467 verde (specs nuevos incluidos), eslint 0 errores,
      build ✓; backend intacto (sin cambios)

## Files to Create
- Specs de stores/vistas afectados (extender `mcpStore.spec.ts`, `chatStore.spec.ts`
  y el spec de la vista de skills)

## Files to Modify
- `frontend/src/stores/mcpStore.ts`, `chatStore.ts`, store de skills (a ubicar)
- `frontend/src/views/ChatView.vue`, `MCPInspectorView.vue`, vista de catálogo de
  skills (a ubicar)
- `frontend/src/locales/en.json`, `frontend/src/locales/es.json`

## Related Issues
- #596 (backend de los 3 DELETE + decisión backend-only → este es su follow-up),
  #576/#577 (patrón de UI real/mock y delete de asignación), #548 (patrón 404 por
  propiedad con JWT), #564 (503 sin backend), #598 (cierre de la tanda)

## Notes
- Verificado 2026-10-26: 0 funciones de delete en los stores; el único borrado en
  real de la UI es `AgentSkillsView:337` (asignaciones).
- Regla heredada de #596: identidad de chat **siempre del JWT** — no exponer en la UI
  borrado de conversaciones ajenas (el backend ya responde 404).
