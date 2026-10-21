# Issue #595: OpenAPI sin `requestBody` documentado en múltiples endpoints + `POST|DELETE /issues/{id}/affects` con cuerpo string crudo

## Description

El contrato OpenAPI/publicado **miente sobre los cuerpos de petición**, con dos
consecuencias medibles:

1. **`requestBody` ausente** en endpoints que sí lo exigen: entre otros, `epics`,
   `objectives`, `secrets`, `flags`, `chat-messages`, `privacy`, `deployments`,
   `registry-schemas` (inventario de la auditoría run4). Efecto práctico: cualquier
   cliente auto-generado (incluido el smoke de la auditoría, que construía bodies con
   `example(schema)`) manda `{}` → y `{}`+`PATCH /epics` = 500 (#579), o 422 varios.
   El OpenAPI es la fuente de verdad y está incompleta.
2. **Contrato inintuitivo en `affects`**: `POST|DELETE /api/v1/issues/{issue_id}/affects`
   declara `symbol_id: str = Body(...)` (`routers/dependencies.py:384-393` y `419-428`),
   o sea que el body debe ser un **string JSON crudo**:
   - `json="smoke-symbol-1"` → pasa la validación y llega al handler (404 si la issue
     no existe — comportamiento correcto verificado el 2026-10-21).
   - `json={"component_id": "..."}` o `{}` → `422 "Input should be a valid string"`
     (loc `["body"]`).
   Ningún otro endpoint de la API usa cuerpo string plano — un cliente que siga el
   patrón del resto (`{"symbol_id": ...}`) recibe 422.

Diagnóstico en run4: el smoke marcó ERR/422 en varias rutas precisamente por esta
cegera entre OpenAPI y validación real (p.ej. `PATCH manifest/todo` mandando lo que el
schema decía sin `requestBody` declarado).

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / API (esquemas y documentación OpenAPI)

## Type
bug fix / docs-backend

## Implementation

1. **Inventario**: extraer del `/openapi.json` vivo los métodos que aceptan body y no
   declaran `requestBody` (el smoke ya tiene el listado en su inventario — reutilizar
   `show_schemas.py`/lógica equivalente de la auditoría) y contrastarlo con los
   `Body(...)`/schemas de los routers.
2. **Declarar schemas**: añadir el `requestBody` con modelo Pydantic a cada endpoint
   afectado (los modelos ya existen en `schemas.py` en la mayoría: `EpicCreate`,
   `ObjectiveCreate`, etc. — es documentación, no lógica nueva).
3. **`affects` — dos opciones** (decidir):
   - **A (recomendada)**: cambiar el contrato a objeto `{"symbol_id": "..."}` con
     `SymbolLinkRequest(BaseModel)` — consistente con el resto de la API;Actualizar
     docs/tests. ⚠️ Rompe consumidores existentes (el CLI
     `cli/commands/agent_commands.py` llama a estas rutas — auditar call-sites).
   - **B**: mantener el string crudo pero **documentarlo** en el `requestBody`
     (schema `type: string` + descripción clara) para que el OpenAPI no mienta.
4. **Tests**:
   - Test de "contrato": cada endpoint con body obligatorio declara `requestBody` en
     `app.openapi()` (un test que recorra las rutas y falle si falta — evita regresión).
   - Tests de `affects` con el contrato elegido (string u objeto) + 422 del formato
     equivocado.

## Acceptance Criteria
- [ ] `GET /openapi.json`: todos los endpoints de escritura con body obligatorio
      declaran `requestBody` con schema real (lista completa auditada)
- [ ] El smoke/clientes auto-generados producen bodies válidos para epics/objectives
      (ya no `{}` silencioso → #579 deja de tener client que lo provoque)
- [ ] `POST|DELETE /issues/{id}/affects`: contrato elegido (objeto `symbol_id` o
      string documentado) y test que lo fije
- [ ] Call-sites del repo (CLI) actualizados si cambia el contrato
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (modelos que faltan)
- Routers: `epic.py`, `objective.py`, `secrets.py`, `flags`, `chat`, `privacy`,
  `deployments`, `registry-schemas`, `routers/dependencies.py` (affects)
- `tests/` — test de contrato OpenAPI

## Related Issues
- #579 (PATCH con `{}` → 500), #586 (`manifest/todo` — su requestBody sí estaba
  documentado y aun así 500: bug de persistencia, separado), #555/#552 (CLI/despliegue
  que consume estas rutas)

## Notes
- Fuente: inventario de la corrida run4 del smoke (`results4.json`, 294 rutas) + repro
  de `affects` con body string vs objeto (2026-10-21, TestClient en contenedor).
- El smoke debe rehacerse tras este fix: hoy su generator de bodies es una
  aproximación a partir de OpenAPI incompleto.
