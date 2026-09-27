# Issue #524: RAG Explorer & MCP Server Integration

## Description

Las vistas `GraphRAGExplorerView` y `MCPInspectorView` dependen de payloads en memoria (`ragStore`/`mcpStore` sembrados). Se debe conectar el RAG Explorer a una base de datos vectorial/grafo real (Neo4j + embeddings) y permitir la inspección en tiempo real de llamadas de herramientas a servidores MCP activos con su depuración de rendimiento.

Origen: `notas.md` → [ISSUE-08] Integración de RAG Explorer y Servidor MCP (→ #524).

## Status: TODO

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
- [ ] RAG Explorer queries a real Neo4j vector/graph database (mock fallback preserved)
- [ ] MCP Inspector shows live tool calls from active MCP servers
- [ ] Per-tool latency, success/error metrics and payload inspection for debugging
- [ ] Re-execute a tool call directly from the inspector
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/api/ragApi.ts`
- `frontend/src/api/mcpApi.ts`

## Files to Modify
- `frontend/src/stores/ragStore.ts` — consultas reales + fallback
- `frontend/src/stores/mcpStore.ts` — sesiones y tool calls en vivo
- `frontend/src/views/GraphRAGExplorerView.vue` — resultados reales
- `frontend/src/views/MCPInspectorView.vue` — modo LIVE + métricas
- `frontend/src/locales/en.json` / `es.json` — rag/mcp live states
- `features.md` — cuando esté done

## Related Issues
- #491 (Graph RAG Explorer), #209 (RAG Native Neo4j Vector Indexes), #301 (Embedding Adapter & FAISS Vector Store), #488 (MCP Live Inspector Control Panel), #472 (Agent Streaming SSE/WebSocket), #517 (Realtime architecture)
