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

## Status: DONE (commit pendiente)

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
- [x] `GET /openapi.json`: todos los endpoints de escritura con body obligatorio
      declaran `requestBody` con schema real (lista completa auditada)
- [x] El smoke/clientes auto-generados producen bodies válidos para epics/objectives
      (ya no `{}` silencioso → #579 deja de tener client que lo provoque)
- [x] `POST|DELETE /issues/{id}/affects`: contrato elegido (objeto `symbol_id` o
      string documentado) y test que lo fije
- [x] Call-sites del repo (CLI) actualizados si cambia el contrato
- [x] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

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

### Resolución (2026-10-22)

**Inventario real (diferente al descrito)**: con `app.openapi()` vivo, 79/79 rutas
con body param de FastAPI ya declaraban `requestBody`; el agujero eran (a)
handlers que leen el body a mano con `await request.body()` sin declarar nada
(`POST /admin/flags`, `POST /privacy/export`, `POST /privacy/delete`,
`POST /models/{name}/infer`, `POST /webhooks/github`) y (b) endpoints que sí
declaraban pero con `body: dict` genérico sin campos (epics x3, objectives x3,
secrets x3, `POST /deployments`). `registry-schemas` no existe en el código
actual (N/A); chat-messages ya usaba modelos tipados.

**Fix 1 — modelos Pydantic nuevos en `schemas.py`** (defaults espejo de los
antiguos `body.get(...)`: documentacion/validacion, no logica):
`FlagSetRequest`, `PrivacyExportRequest`/`PrivacyDeleteRequest`,
`EpicCreateRequest`/`EpicUpdateRequest`/`EpicLinkIssuesRequest`,
`ObjectiveCreateRequest`/`ObjectiveUpdateRequest`/`ObjectiveLinkEpicsRequest`,
`SecretPutRequest`/`SecretRotateScheduleRequest`/`SecretRotateRunRequest`,
`DeploymentCreateRequest`, `SymbolLinkRequest`. Los UPDATE llevan
`extra="allow"` + `model_dump(exclude_none=True)` para preservar el passthrough
al mixin y el 422 "empty update" de #579. `POST /models/{name}/infer` reutiliza
`ml.schemas.InferenceRequest` (ya existia). `POST /webhooks/github` (lee bytes
crudos para HMAC) declara `requestBody` via `openapi_extra` sin tocar el
handler. `POST /admin/flags` conserva el 400 "missing name" (lo fija
`test_api_set_flag_missing_name`) → `name` opcional en su modelo.

**Fix 2 — `affects` → Opcion A (objeto)**: `add_affects_symbol` /
`remove_affects_symbol` en `routers/dependencies.py` reciben ahora
`payload: SymbolLinkRequest`. Auditoria de call-sites:
`infrastructure/api_repository.py:148,168` YA enviaba
`json={"symbol_id": ...}` — estaba roto contra el validador viejo (422 latente)
y ahora cuadra; `docs/api_contract.md` ya documentaba el objeto (se anadio la
seccion DELETE que faltaba); **el CLI NO llama a estas rutas** (el `--affects`
de `issue_commands.py` es otra cosa); unico consumidor del string era
`tests/api/test_cypher_param_smoke.py`, actualizado al objeto.

**Tests**: nuevo `tests/api/test_openapi_contract.py` (25): loop global
`route.dependant.body_params` → exige `requestBody` en `app.openapi()`
(regresion); parametrizado sobre los 16 (metodo, path) auditados → `$ref` a
schema nombrado presente en components; `SymbolLinkRequest` exige `symbol_id`;
affects con spy repo (objeto → 200 con efecto, string → 422, `{}` → 422,
issue inexistente → 404); `POST /epics {}` → 400 de validacion de dominio del
Epic (nombre min_length=1 — comportamiento preexistente preservado).

**Verificacion en vivo** (tasker-api reconstruido, 2026-10-22): 18/18 —
openapi.json con los 16 `$ref` nombrados + `SymbolLinkRequest` requerido;
affects objeto → 404 ISSUE_NOT_FOUND (validacion pasa) y string → 422 en
POST y DELETE; `POST /epics` modelo tipado → 201 con GET/DELETE de limpieza;
flags con JWT admin → 200 con nombre y 400 sin nombre; infer `{}` → 400
"missing features or key" (modelo aceptado); secrets put+rotate → 200 con
borrado de limpieza; nodos Neo4j 5 → 5; `docker logs` sin ERROR/Traceback.
Fuera de alcance vivo: privacy (sus handlers usan solo `verify_token`
estatico → inalcanzables con JWT, gap de auth distinto ya visto en #593;
cubierto por openapi + unit) y `POST /deployments` (crea nodos; solo
openapi + unit).

**Gates**: ruff (9 ficheros) HEAD 101 → 97 (delta −4), `mypy src/` 1102
(HEAD 1110, −8), `pytest -q` **1647 passed / 62 skipped / 0 failed**
(+25 tests nuevos).
