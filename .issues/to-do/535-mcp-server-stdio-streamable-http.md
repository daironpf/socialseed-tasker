# Issue #535: Servidor MCP real (stdio/HTTP) para Cursor y Claude Desktop

## Description

El "servidor MCP" actual es un registry en proceso (`routers/mcp.py`, #524) con endpoints REST + stream SSE para el inspector: no hay transporte MCP real, así que clientes como Cursor o Claude Desktop no pueden conectarse. La ÉPICA 6 de `notas.md` pide exponer la estructura del grafo mediante el estándar MCP para que esos clientes consulten la arquitectura, componentes, issues bloqueados y políticas activas directamente, sin configuraciones adicionales. Este gap está declarado en `features.md` §50 ("MCP servers run in-process").

Origen: `notas.md` → ÉPICA 6 · Issue #14 (→ #535).

## Status: TODO

## Priority: MEDIUM

## Component
Backend / AI / MCP / Integration

## Type
feat / ai infrastructure

## Implementation
1. **Servidor MCP:** nuevo entrypoint (`entrypoints/mcp_server.py` o mount en la API) sobre el SDK `mcp` con transporte **streamable HTTP** (montado en la API, p.ej. `/mcp`) y/o binario **stdio** para clientes locales; `initialize`, `tools/list` y `tools/call` según spec MCP.
2. **Tools sobre el grafo (Neo4j):** `graph_architecture` (nodos/aristas de componentes), `list_components`, `blocked_issues`, `active_policies`, `issue_detail`, `dependency_impact` — reutilizando repositorios/casos de uso existentes.
3. **Seguridad:** en HTTP aplica el mismo guard de API key/JWT que el resto de la API; en stdio no se vierten secretos por stdout.
4. **Configuración de clientes:** snippet documentado para `claude_desktop_config.json` y Cursor (URL/comando + API key) con un ejemplo de uso ("¿qué issues están bloqueados hoy?").
5. **Inspector:** las sesiones/herramientas invocadas por clientes externos quedan visibles (o auditables) desde el inspector MCP de #524.

## Acceptance Criteria
- [ ] Endpoint/servicio compatible con la especificación MCP, expuesto por transporte real (HTTP o stdio)
- [ ] Clientes MCP consultan arquitectura, componentes, issues bloqueados y políticas activas sin configuración adicional más allá de la URL/comando
- [ ] Configuración de ejemplo para Cursor y Claude Desktop documentada
- [ ] Llamadas de clientes externos visibles/auditables desde el inspector MCP
- [ ] Tests del handshake/tools; gates backend sin regresiones

## Files to Create
- `src/socialseed_tasker/entrypoints/mcp_server.py`
- `tests/api/test_mcp_server_protocol.py`

## Files to Modify
- `pyproject.toml` — dependencia `mcp`
- `src/socialseed_tasker/infrastructure/web_api/routers/mcp.py` — exposición/inspección de sesiones externas
- `docker-compose.yml` — puerto/flag del servidor MCP (si HTTP)
- `README`/docs — configuración para Cursor/Claude Desktop
- `features.md` — §68 + §50 (gap de procesos externos eliminado)

## Related Issues
- #488 (MCP live inspector control panel), #524 (MCP registry + SSE + rerun), #487 (Agent creation), #222 (Architect agent), #472 (Agent streaming)
