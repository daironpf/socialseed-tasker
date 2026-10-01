# Issue #535: Servidor MCP real (stdio/HTTP) para Cursor y Claude Desktop

## Description

El "servidor MCP" actual es un registry en proceso (`routers/mcp.py`, #524) con endpoints REST + stream SSE para el inspector: no hay transporte MCP real, así que clientes como Cursor o Claude Desktop no pueden conectarse. La ÉPICA 6 de `notas.md` pide exponer la estructura del grafo mediante el estándar MCP para que esos clientes consulten la arquitectura, componentes, issues bloqueados y políticas activas directamente, sin configuraciones adicionales. Este gap está declarado en `features.md` §50 ("MCP servers run in-process").

Origen: `notas.md` → ÉPICA 6 · Issue #14 (→ #535).

## Status: DONE

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
- [x] Endpoint/servicio compatible con la especificación MCP, expuesto por transporte real (HTTP o stdio)
- [x] Clientes MCP consultan arquitectura, componentes, issues bloqueados y políticas activas sin configuración adicional más allá de la URL/comando
- [x] Configuración de ejemplo para Cursor y Claude Desktop documentada
- [x] Llamadas de clientes externos visibles/auditables desde el inspector MCP
- [x] Tests del handshake/tools; gates backend sin regresiones

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

## Verification

- **Transporte HTTP:** `entrypoints/mcp_server.py` monta `streamable_http_app` (stateless, JSON, sin protección DNS-rebinding) en `/mcp`; el session manager corre en el lifespan raíz de `app.py`. Handshake en proceso y en Docker: `initialize` 200, `notifications/initialized` 202, `tools/list` 200 (6 tools), `tools/call` 200; rutas desconocidas 404; sin `X-API-Key` 401.
- **Transporte stdio:** consola `tasker-mcp` (`Container.from_env()`, Neo4j directo, sin secretos por stdout).
- **Inspector:** `tasker-mcp` registrado como servidor online y cada llamada externa auditada con sesión `ext-<sha1[:12]>` (verificado en vivo: `GET /api/v1/mcp/servers` + `/api/v1/mcp/tool-calls` → `blocked_issues` success).
- **Docs:** README sección "MCP clients (Cursor / Claude Desktop)" con snippets para Cursor/Claude Desktop (URL + API key y comando `tasker-mcp`); `features.md` §50 (gap "in-process" reformulado) y §68 (fila `MCP server (#535)`); INDEX 11/11.
- **Tests:** `tests/api/test_mcp_server_protocol.py` 10 nuevos (handshake, tools, errores, inspector, auditoría, auth) + `test_mcp_api_unit` ajustado por el registro de `tasker-mcp`.
- **Gates:** `ruff check src/` 1011 (baseline), `mypy src/` 1152/133 (idéntico al worktree HEAD, +0 de source), `pytest -q` 1206 passed / 27 skipped / 6 failed (3 preexistentes: delivery_retry + 2× tasks; 3 por entorno: Hyper-V excluye los puertos TCP 8946–9145, que cubre el 9010 del contract mock server — también falla en HEAD).
