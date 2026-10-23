# Issue #596: Faltan endpoints `DELETE` — `skills`, `mcp/servers` y `chat/conversations` no se pueden dar de baja vía API

## Description

Tres colecciones tienen lectura/creación pero **no borrado**, dejando "basura
permanente" que solo se puede limpiar tocando la base a mano:

| Superficie | Que existe hoy | Que falta |
|---|---|---|
| Skills (catálogo) | `GET /skills` (#572), `POST /skills` (#576) | `DELETE /skills/{skill_id}` |
| MCP servers | `GET/POST /mcp/servers` (+ detalle) | `DELETE /mcp/servers/{id}` |
| Chat conversations | `GET /chat/conversations`, `POST` (Mongo, #537/#551) | `DELETE /chat/conversations/{id}` |

(Inventario de la auditoría run4 de las 294 rutas del backend real — grep de métodos
por recurso.)

Impacto:

- **Skills**: `POST /skills` (#576) permite crear skills mal escritas desde la UI y no
  hay forma de retirarlas del catálogo; `user_skills`/`agent_user_skills` (#576/#577)
  quedan con links a la skill.
- **MCP servers**: alta de servidores de prueba sin baja → crecimiento sucio del
  catálogo que consume la UI de MCP.
- **Conversaciones de chat**: el wipe de Mongo (`setup_initialize`, #543/#549) es la
  única limpieza — el usuario no puede borrar una conversación suya desde la API.

## Status: DONE (2026-10-23)

## Priority: MEDIUM

## Component
Backend / API (catalogs + MCP + chat Mongo)

## Type
feat / backend

## Implementation

1. **`DELETE /skills/{skill_id}`** (`routers/catalogs.py`, junto al `POST /skills` de
   #576):
   - Borrar del catálogo + **cascada de asignaciones** (`user_skills`,
     `agent_user_skills` — patrón de `delete_agent_skill` de #577: las asignaciones se
     van, el catálogo muere).
   - 404 si no existe; 200 con confirmación; 503 sin `TASKER_DATABASE_URL` (patrón
     #564/#572/#576).
   - Decidir si una skill **en uso** se puede borrar (cascada total vs 409) —
     recomendación: cascada total con el detalle de cuántas asignaciones se borraron
     (mismo criterio que agent-skills).
2. **`DELETE /mcp/servers/{id}`** (router MCP existente): patrón idéntico a sus
   endpoints vecinos (404/503), borrar también su detalle/cascadas si las tiene
   (revisar el alta `POST /mcp/servers` para no dejar filas huérfanas).
3. **`DELETE /chat/conversations/{id}`** (router `chat.py`):
   - Identidad **siempre del JWT** (`_current_user` — patrón de #548: una conversación
     ajena → 404 sin filtrar existencia).
   - Mongo: borrar la conversación y sus mensajes (`ChatMongoRepository`, patrón
     `NotificationMongoRepository.delete` de #548) — `ChatStoreError` → 503
     degradado.
   - 404 si no existe o es de otro usuario; 200 con confirmación.
4. **Frontend** (si aplica en esta tanda — los menús de borrado ya existen en las
   vistas de skills/MCP/chat en modo mock):
   - Cablear los botones existentes al DELETE en modo real (patrón `isMockMode()` de
     #576/#577), con confirmación y refetch.
   - i18n EN/ES de cualquier texto nuevo (paridad).
5. **Tests**:
   - Backend: `test_delete_skill_cascades_assignments` (404, 503),
     `test_delete_mcp_server_404_200`, `test_delete_conversation_owner_only` (ajeno →
     404) + `test_delete_conversation_503_without_mongo`.
   - Frontend: specs de los bots en real/mock si se cablean.

## Acceptance Criteria
- [x] `DELETE /skills/{id}` → 200 y desaparece de `GET /skills` con sus asignaciones
      limpiadas; 404/503
- [x] `DELETE /mcp/servers/{id}` → 200/404 (503 sin backend)
- [x] `DELETE /chat/conversations/{id}` → 200 solo para el dueño (JWT); ajeno/inexistente
      → 404; Mongo caído → 503
- [x] Los bots de borrado de la UI funcionan en modo real — **fuera de alcance en esta
      tanda** (decisión explícita: backend-only; cableado de UI queda como follow-up)
- [x] i18n EN+ES — no aplica (sin UI en esta tanda)
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas; frontend lint/test/build
      no aplica (sin UI)

## Files to Create
- `tests/api/test_delete_endpoints.py` (o los que correspondan por router)
- (si aplica) specs frontend de los bots

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/catalogs.py` (DELETE /skills)
- `src/socialseed_tasker/infrastructure/web_api/routers/` — router MCP
- `src/socialseed_tasker/infrastructure/web_api/routers/chat.py` (DELETE conversación)
- `src/socialseed_tasker/auth/user_store.py` (cascada de skills, patrón #577)
- `src/socialseed_tasker/infrastructure/mongo/chat_repository.py` (delete)
- Frontend: vistas de Skills/MCP/Chat (modo real) + `frontend/src/locales/es.json`/`en.json`

## Related Issues
- #572/#576 (skills GET/POST), #577 (cascada de `agent_skills` como precedente),
  #537/#551 (chat Mongo), #548 (patrón DELETE con identidad JWT), #564 (503 sin DB)

## Notes
- No confundir con `DELETE /users/{id}/skills/{skill_id}` (#576): eso borra la
  **asignación**; aquí se trata el **catálogo**.
- El patrón de "propiedad por JWT y 404 sin filtro de existencia" ya está escrito en
  `notifications.py` — copiarlo, no inventar.

## Resolución (2026-10-23)

**Fix:** los tres DELETE faltantes + cascadas.

- `user_store.py::delete_skill(skill_id)` (transacción: existencia → count de
  `user_skills` → DELETE del catálogo; `None` = 404) + `DELETE /skills/{skill_id}` en
  `routers/catalogs.py` → 200 `{deleted, assignmentsRemoved}` / 404 / 503 sin PG.
  Cascada `user_skills` (DDL #558 `ON DELETE CASCADE`; `agent_user_skills` apunta a
  `agent_skills`, catálogo distinto — fuera de este borrado).
- `MCPRegistry.remove_server(server_id)` en `routers/mcp.py`: hace pop del server,
  **cascada de sesiones huérfanas** por `server in (id, nombre)` con eventos
  `session_removed` + `server_removed`; `DELETE /mcp/servers/{server_id}` →
  200 `{id, sessionsRemoved}` / 404 (patrón idéntico a `delete_session` vecino).
- `ChatMongoRepository.delete_conversation(id)` (borra el doc y sus `messages`,
  wrap `ChatStoreError`) + `DELETE /chat/conversations/{id}` en `routers/chat.py`:
  identidad por `_current_user`, **404 para ajeno/inexistente/invalid** (sin filtrar
  existencia, a diferencia del 403 de `_owned_conversation` — criterio de la issue),
  503 degradado/sin store.
- Tests: `tests/api/test_delete_endpoints.py` (10: cascada skills 404 503, MCP
  cascada+404, chat dueño/ajeno/inválido/401/503/degradado) + 3 handlers nuevos en
  `FakePgCursor` (existencia skills por id, count de asignaciones, delete con poda
  de sets vacíos).
- **Gates:** ruff "All checks passed!" (0 delta), mypy **1102** (= baseline), pytest
  **1657 passed / 62 skipped / 0 failed** (+10).
- **Verificación en vivo** (rebuild `tasker-api`, `verify_596_live.py`, 24/24): delete
  con cascade `assignmentsRemoved: 1`, 404 x2, 401 sin JWT; MCP `sessionsRemoved: "1"`
  + sesión fuera de `GET /mcp/sessions` + 404; chat dueño 200, 404 ajeno/inválido,
  401 sin token; neo4j 5→5; `docker logs` sin ERROR/Traceback.
- **Frontend:** fuera de alcance (decisión del usuario: backend-only — los stores no
  tienen funciones de delete; cableado de bots queda como follow-up).
