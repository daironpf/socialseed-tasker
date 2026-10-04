# Issue #546: Configuración de credenciales de IA y servidores MCP en el Setup Wizard

## Description

Para que Tasker sea un sistema de gobernanza nativo para IA desde el minuto cero, el Setup Wizard debe ofrecer configurar los tokens y servidores MCP (*Model Context Protocol*) que usarán los agentes autónomos (Cursor, Claude, Windsurf, LangChain): generación de una Master API Key para los agentes y snippet de integración listo para pegar en la configuración del cliente.

Contexto real del repo: el servidor MCP real (streamable HTTP en `/mcp` + stdio, #535) ya existe y se autentica con `X-API-Key` (hoy la env `TASKER_API_KEY`); hay un router `secrets.py` (gestor de secretos, #97/#106) disponible para persistir la key generada, y el payload mínimo de `POST /setup/initialize` (#543) debe ampliarse con campos opcionales sin romper el contrato.

Origen: `notas.md` → Épica Flow de Onboarding & Setup Wizard Empresarial · Issue #5 (→ #546).

## Status: DONE (2026-10-04)

## Priority: MEDIUM

## Component
Frontend / AI / MCP / Enterprise

## Type
feat / enterprise

## Implementation
1. **Ampliación del payload de inicialización (`SetupPayload`):** campos opcionales `api_key` (clave maestra para autenticación de agentes) y `mcp_port` (puerto del servidor MCP Inspector / Server), con defaults cuando no se envían (compatibilidad con el contrato mínimo de #543).
2. **Generación y persistencia de la API Key:** clave aleatoria con formato `tasker_sk_live_...` generada e inicializada en el backend (gestor de secretos existente `routers/secrets.py` o almacenamiento seguro equivalente), devuelta en la respuesta de `initialize` solo al completar la instalación.
3. **UI — paso opcional en el Setup Wizard:** panel "Credenciales de IA" al final del wizard (#545): muestra la Master API Key con botón de copiar al portapapeles (feedback visual de copiado) y campo de puerto MCP configurable.
4. **Snippet de integración:** bloque de código listo para pegar en `.cursor/mcp.json` o `.windsurf/mcp.json` apuntando al endpoint `/mcp` del servidor MCP (#535) con la cabecera `X-API-Key` (URL de la API derivada de `window.__API_URL__`), con botón de copiar.
5. **i18n:** etiquetas del paso/panel EN + ES (ASCII en ES).
6. **Tests:** spec del panel (generación/copia/snippet) + test backend de los campos opcionales del payload.

## Acceptance Criteria
- [x] El usuario obtiene una Master API Key activa (`tasker_sk_live_...`) con botón para copiar al portapapeles al finalizar la instalación inicial
- [x] Se muestra un snippet de configuración listo para pegar en `.cursor/mcp.json` o `.windsurf/mcp.json`
- [x] El puerto del servidor MCP es configurable desde el wizard
- [x] `SetupPayload` acepta los campos opcionales sin romper el flujo mínimo (`admin`/`admin` de #543 sigue funcionando)
- [x] i18n EN+ES y gates backend/frontend sin regresiones

## Files to Create
- `frontend/src/components/setup/McpSetupPanel.vue`
- `frontend/src/components/setup/McpSetupPanel.spec.ts`

## Files to Modify
- `frontend/src/views/SetupWizardView.vue` — paso/panel opcional de credenciales IA
- `frontend/src/api/setupApi.ts` — payload extendido (`api_key`, `mcp_port`)
- `src/socialseed_tasker/infrastructure/web_api/routers/setup.py` — campos opcionales + generación/persistencia de la key
- `src/socialseed_tasker/infrastructure/web_api/routers/secrets.py` — alta/consulta de la Master API Key
- `frontend/src/locales/en.json` / `es.json` — claves del panel

## Related Issues
- #535 (servidor MCP `/mcp` + auth `X-API-Key`), #97/#106 (gestor de secretos), #543 (payload base de initialize), #545 (wizard que aloja el paso), #69 (API key auth del backend)
