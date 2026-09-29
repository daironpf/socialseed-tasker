# Issue #524: RAG Explorer & MCP Server Integration

## Description

Las vistas `GraphRAGExplorerView` y `MCPInspectorView` dependen de payloads en memoria (`ragStore`/`mcpStore` sembrados). Se debe conectar el RAG Explorer a una base de datos vectorial/grafo real (Neo4j + embeddings) y permitir la inspección en tiempo real de llamadas de herramientas a servidores MCP activos con su depuración de rendimiento.

Origen: `notas.md` → [ISSUE-08] Integración de RAG Explorer y Servidor MCP (→ #524).

## Status: DONE (2026-09-28)

## Priority: MEDIUM

## Component
Frontend / AI Infrastructure / RAG / MCP

## Type
feat / ai infrastructure

## Implementation
1. **RAG real:** `api/ragApi.ts` contra `/api/v1/rag/*` (el backend ya soporta índices vectoriales nativos de Neo4j, #209); `ragStore` consulta el endpoint real con fallback mock (flag de #517); la UI muestra chunks/nodos recuperados, scores y trazas desde la respuesta real, no fixtures.
2. **MCP en vivo:** `api/mcpApi.ts`: listar servidores/sesiones MCP activas, suscripción a llamadas de herramientas en curso (stream de #517 o polling), historial de sesiones; `MCPInspectorView` con modo LIVE vs MOCK e indicador de conexión.
3. **Depuración de rendimiento:** tabla de latencias por tool (duración, éxitos/errores), detección de tools lentas, payload redactado y botón *Re-run tool* para re-ejecutar una llamada desde el inspector.
4. i18n + build + smoke contra backend Docker.

## Acceptance Criteria
- [x] RAG Explorer queries a real Neo4j vector/graph database (mock fallback preserved)
- [x] MCP Inspector shows live tool calls from active MCP servers
- [x] Per-tool latency, success/error metrics and payload inspection for debugging
- [x] Re-execute a tool call directly from the inspector
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Files to Create
- `frontend/src/api/ragApi.ts`
- `frontend/src/api/mcpApi.ts`
- `src/socialseed_tasker/infrastructure/web_api/routers/mcp.py` (registro MCP + 9 endpoints + SSE + rerun)
- `tests/api/test_mcp_api_unit.py` (13 tests)
- `frontend/src/stores/ragStore.spec.ts` / `frontend/src/stores/mcpStore.spec.ts` / `frontend/src/views/MCPInspectorView.spec.ts`

## Files to Modify
- `frontend/src/stores/ragStore.ts` — consultas reales + fallback
- `frontend/src/stores/mcpStore.ts` — sesiones y tool calls en vivo
- `frontend/src/views/GraphRAGExplorerView.vue` — resultados reales
- `frontend/src/views/MCPInspectorView.vue` — modo LIVE + métricas
- `frontend/src/types/mcp.ts` — tipos `MCPServer`/`MCPToolCall`/`MCPToolMetric`
- `frontend/src/utils/pendingFeatures.ts` — `/rag` y `/mcp` ya no son pendientes
- `frontend/src/locales/en.json` / `es.json` — rag/mcp live states (+ fix `mcp.avgPerMin` `{{rate}}` → `{rate}`)
- `src/.../routers/__init__.py` / `web_api/routes.py` / `web_api/app.py` — registro del router
- `features.md` — §68 + §50 cuando esté done

## Related Issues
- #491 (Graph RAG Explorer), #209 (RAG Native Neo4j Vector Indexes), #301 (Embedding Adapter & FAISS Vector Store), #488 (MCP Live Inspector Control Panel), #472 (Agent Streaming SSE/WebSocket), #517 (Realtime architecture)

## Verification (2026-09-28)
- Backend gates en baseline: `ruff check src/` 1011, `mypy src/` 1158 errores / 133 ficheros, `pytest -q` 1093 passed / 27 skipped / 3 fallos preexistentes (reproducidos con los cambios stash)
- Nuevos `tests/api/test_mcp_api_unit.py`: 13/13 (registry, sesiones, filtros+422, redacción, rerun 404/400/success/error, SSE invocando `stream_tool_calls(Request(scope))` directamente porque `TestClient.stream` cuelga en cualquier endpoint SSE de este entorno)
- Frontend: `npm run lint` 0 errores (2 warnings preexistentes), `npm test` 158/158 (20 ficheros; +18 nuevos: ragStore 6, mcpStore 9, MCPInspectorView 3), `npm run build` verde (vue-tsc + vite)
- Docker: `docker compose build tasker-api tasker-board` + `up -d`; smoke en :19001 → index 200, bundle contiene `MCP Servers`, `Latency by Tool`, `Re-run tool`, `Payload Inspection`, `Graph RAG Explorer`; `GET /api/v1/mcp/{servers,sessions,tool-calls}` → 200 con envelope; `GET /api/v1/rag/stats` → `{"total":0,"by_type":{}}`; `POST /api/v1/rag/search` → `{"results":[],"count":0}` (sin `OPENAI_API_KEY` → estado de error/vacío visible en la UI); SSE `/api/v1/mcp/tool-calls/stream` → `event: connected` + snapshot `tool_calls`
- `features.md` §68 añadida; §50 actualizada (gap RAG eliminado, gap MCP acotado a procesos externos)
