# Issue #604: Eliminar los hallazgos de Ruff en `src/`

## Description

La revisión del proyecto encontró **986 hallazgos de Ruff en `src/`**, incluidos
**7 `F821`** por nombres indefinidos. La tanda de correcciones posterior resolvió
varios casos confirmados en CLI, wiring, routers y el parser, pero no es una limpieza
completa del baseline: queda deuda en varias reglas y módulos.

El objetivo es eliminar todos los hallazgos bajo la configuración Ruff vigente para
`src/`, en lotes revisables, sin esconder el baseline con ignores ni cambiar el
comportamiento del proyecto.

## Status: DONE

## Priority: MEDIUM

## Component
Backend / calidad estática (Ruff)

## Type
quality / backend

## Implementation

1. **Fijar el baseline vigente**: ejecutar `ruff check src/ --statistics` y guardar el
   total y los conteos por regla antes de modificar código. Los 986 hallazgos
   anteriores son referencia histórica, no asumir que siguen siendo el total exacto.
2. Corregir primero los errores con riesgo de fallo en ejecución, incluidos todos los
   `F821`; verificar las referencias con imports y contratos reales. No sustituir
   símbolos por `Any` ni añadir imports que oculten dependencias incorrectas.
3. Corregir los hallazgos restantes de las reglas activas en `pyproject.toml` sobre
   todo `src/`, por lotes revisables, ejecutando pruebas enfocadas y registrando el
   delta de cada lote.
4. No aplicar autofixes globales sin revisar el diff; conservar los comportamientos y
   solo mantener excepciones locales justificadas que ya sean necesarias.

## Acceptance Criteria
- [x] `ruff check src/` termina con cero hallazgos bajo las reglas configuradas.
- [x] `ruff check src/ --select F821` termina con cero hallazgos.
- [x] Las pruebas enfocadas de todos los módulos modificados pasan.
- [x] No se añaden ignores globales, no se deshabilitan reglas y no se introduce
      reformateo ajeno a la corrección.
- [x] La resolución registra baseline, total final cero, comandos y pruebas ejecutadas.

## Resolution

Baseline vigente medido al empezar (config de `pyproject.toml`): **904 hallazgos**,
**0 `F821`**, 129 ficheros. Orden de trabajo y delta por lote (siempre con
`ruff check src/ --statistics` tras cada paso):

1. **Mecánicos revisados** (447 + 9 + 109 + 11): `I001,UP006,UP045,UP037,F401,F541,F811,E401,W292,UP015,UP012`
   → 447; `UP035,SIM117` → 9; `W293,W291` (unsafe) → 109; `F841` (unsafe) → 11 más
   3 sentencias muertas eliminadas a mano en `ml/server.py` y
   `web_api/app.py` (cálculos de latencia y `field_path` sin efecto).
2. **Semánticos**: `SIM105/SIM108/E731` (22, unsafe), `E702` (16 tablas Rich
   partidas), `E741`, `B007`, `B905` (`strict=False`), `N806`
   (`_SSO_RETIRED`→`_sso_retired`, `_REDIS_AVAILABLE`→`_redis_available`,
   `reasoningLogs`→`reasoning_logs`, `D`/`I`→`distances`/`indices`), `N814`
   (`JSVE`→`JsonSchemaValidationError`) y `B904` (16 sitios con `from e`/`from None`).
3. **B008 (159)**: solo las filas marcadas (155 `Depends`, 3 `Query`, 1 `Body`) se
   migraron a `Annotated[...]`; se reordenaron 40 parámetros en 38 funciones de 24
   routers para respetar el orden obligatorio/opcional. Casos manuales:
   `commit.py` (`since`/`until` → `Annotated[datetime | None, Query(...)] = None`) e
   `issues.py` (`close_issue.affected_files` → `Body(default_factory=list, ...)`,
   movido antes de `commit_sha`). FastAPI no admite el default dentro de
   `Annotated[..., Query(...)]`; se mantiene fuera. OpenAPI sigue generando 237
   paths y las llamadas directas a handlers no pasan parámetros posicionales.
4. **N803 (26)**: parámetros de `neo4j_impl/component_mixin.py` y `epic_mixin.py`
   renombrados a snake_case (sin call-sites con keyword) y 4 `# noqa: N803` locales
   en `graphql/resolvers.py` porque `schema.graphql` fija `issueId`/`maxDepth`.
5. **N815 (17)**: `# noqa: N815` local en los campos de `ProjectCreateRequest`/
   `ProjectResponse` (`schemas.py`); el contrato JSON es camelCase y los nodos
   Neo4j conservan sus propiedades camelCase (`repositoryUrl`, `techStack`, …).
6. **E501 (68) + SIM115 (1)**: líneas partidas con validación de longitud/indentación
   y `with open(...)` en `cli/commands/constraints_commands.py`.

Resultado final:

- `ruff check src/` → **All checks passed** (0 hallazgos); `ruff check src/ --select F821`
  → 0. Sin cambios en `pyproject.toml` ni ignores globales; únicas excepciones son
  los `# noqa` locales justificados de N803/N815.
- `pytest -q --no-cov` → **1712 passed, 62 skipped, 0 failed** (318 s); subconjunto
  `tests/unit tests/infrastructure tests/api` → **1504 passed**.
- `mypy src` → **1052 errores** en 129 ficheros (antes 1053; gate ≤1100 intacto, la
  deuda restante queda en #605).
- Verificación viva: imagen `tasker-api:local` reconstruida y contenedor `healthy`;
  `GET /openapi.json` 237 paths; login, `/auth/me`, `/issues`, `/projects` y
  `/code-graph/calls/{name}` OK; semántica de parámetros preservada
  (`/ai/search-context` 422 sin `q` y 200 con `q`; `/commits/stats` 200 con y sin
  `since`/`until`; `POST /issues/{id}/close` sin `affected_files` llega al handler y
  responde 404, no 422). Sin errores nuevos en los logs del contenedor.


## Files to Modify
- `src/` — módulos afectados por las reglas Ruff activas
- `pyproject.toml` — referencia de reglas Ruff; no relajarlas para cerrar la issue
- `tests/` — pruebas de regresión para los fallos de ejecución que se corrijan

## Related Issues
- #603 (smoke reproducible y gates enfocados)
- Revisión general del proyecto: baseline inicial de 986 hallazgos y recomendación de
  eliminar la deuda estática incrementalmente

## Notes
- La revisión inicial observó 7 `F821`; varios estaban en las áreas tocadas por la
  corrección de imports y tipos. Recalcular el estado al comenzar; no asumir que esos
  7 siguen abiertos.
- El baseline se mide de nuevo al comenzar porque ya se aplicaron fixes puntuales en
  CLI, wiring, routers y el parser.
