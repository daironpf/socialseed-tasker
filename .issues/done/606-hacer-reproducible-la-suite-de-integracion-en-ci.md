# Issue #606: Hacer reproducible la suite de integración en CI

## Description

La suite marcada como integración no comparte un único requisito externo. La
configuración actual del job de CI provisiona Neo4j, mientras que los tests recopilados
también esperan servicios/endpoints como la API en `localhost:8000`, el board en
`:8080`, Graphviz en `:8082` y Jaeger en `:16686`. En la ejecución local de la
revisión, la suite se detuvo porque la API no estaba disponible; se recopilaron
**31 tests de integración**.

No se debe convertir la suite completa en un gate obligatorio hasta que sus
prerrequisitos sean reproducibles. Hay que separar las pruebas por servicios requeridos
o provisionar el stack necesario dentro del job opt-in.

## Status: DONE — 2026-10-28

## Priority: MEDIUM

## Component
CI / pruebas de integración

## Type
test / infra

## Implementation

1. Inventariar los tests de integración y documentar, por test o grupo, cada servicio,
   puerto, variable de entorno y dato de prueba requerido.
2. Separar las pruebas que solo necesitan Neo4j de las que requieren la API, board,
   Graphviz, Jaeger u otros servicios; usar markers/selectores explícitos y
   descriptivos si los prerrequisitos difieren.
3. Para cada job opt-in, levantar los servicios necesarios con configuración
   reproducible y health checks; esperar disponibilidad antes de ejecutar pytest.
4. Mantener el job desactivado por defecto mientras no sea reproducible. Una vez
   estable, documentar cómo habilitarlo y qué cobertura ejecuta.

## Acceptance Criteria
- [x] Todos los tests de integración están asociados a prerrequisitos claros y
      verificables; no dependen de servicios locales implícitos.
- [x] El job opt-in provisiona el stack y espera los servicios requeridos antes de
      ejecutar sus selectores de integración; el job permanece desactivado por
      defecto.
- [x] Los tests unitarios continúan excluyendo la integración externa y pasan sin
      necesitar los servicios del job opt-in; el comando completo
      `pytest -q -k "not integration" --maxfail=1 --disable-warnings` pasa, no solo
      pruebas focalizadas.
- [x] No se hace obligatoria la suite completa hasta que el job cubra los servicios
      que realmente consume.
- [x] La documentación de CI indica cómo ejecutar localmente los mismos grupos de
      pruebas.

## Files to Modify
- `.github/workflows/ci.yml`
- `pyproject.toml` — markers/selectores si son necesarios
- `tests/integration/` — markers, fixtures o configuración de servicios
- Documentación de contribución/CI existente

## Related Issues
- #603 (smoke API reproducible, independiente de esta suite de integración)
- Revisión general del proyecto: job actual provisiona solo Neo4j y la suite usa
  endpoints externos adicionales

## Notes
- Evidencia local de la revisión: la suite integra expectativas de API `:8000`,
  board `:8080`, Graphviz `:8082` y Jaeger `:16686`; el API no estaba levantado en
  ese entorno.
- La ejecución previa del conjunto no integrado se detuvo tras 503 pruebas aprobadas
  al encontrar un fallo de expectativa en `/auth/me`. La repetición final del comando
  completo terminó con 1708 pruebas aprobadas y 66 tests de integración excluidos.
- No confundir este trabajo con el harness autenticado de #603: son pruebas y
  entornos diferentes.

## Resolution

- Se inventariaron los 31 archivos de integración (62 tests) y se documentaron sus
  markers, servicios, puertos, variables de entorno, selectores locales y el
  carácter destructivo de las pruebas que limpian Neo4j.
- Se añadieron los markers `integration`, `self_contained` y `requires_*` en
  `pyproject.toml`, con `tests/integration/conftest.py` omitiendo el grupo salvo
  `TASKER_INTEGRATION=1`. `pytest -m "not integration"` ya no recolecta ninguno.
- Se configuró el job `integration` como opt-in en `.github/workflows/ci.yml`. El
  job levanta un stack desechable, espera disponibilidad de los servicios, excluye
  los grupos manuales de chaos/tree-sitter y recopila logs si falla.
- `compose/ci/integration.yml` ajusta el stack para el job (auth desactivada,
  `TASKER_INTEGRATION=1`, Jaeger y puertos de host). Se corrigieron rutas de
  provisioning de Grafana/Prometheus que apuntaban a directorios inexistentes.
- Fallos reales descubiertos al reproducir la suite y corregidos:
  - `tools/contracts/mockctl.py` terminaba y mataba el hilo daemon del mock.
  - El exporter de métricas servía el registry por defecto, no el propio.
  - El CLI no sembraba permisos RBAC desde `users.json` cuando no había
    `TASKER_AUTH_USERS`, por lo que el token admin quedaba en `forbidden`.
  - `test_contracts_integration` usaba `localhost` (resolución IPv6) y no esperaba
    al mock; `test_webhooks_integration` competía con el primer ciclo del worker;
    `test_retention_integration` fijaba `TASKER_RETENTION_STORAGE=0` para hacer
    determinista la rama de storage; `test_cli_integration` esperaba `SystemExit`
    en el camino feliz y no autenticaba.
- Verificación local:
  - `pytest -q -k "not integration" --maxfail=1 --disable-warnings` → 1708 passed,
    66 deselected.
  - `pytest -m self_contained` → 26 passed.
  - `pytest -m "requires_neo4j and not requires_celery"` contra Neo4j desechable →
    21 passed.
  - `pytest -m "requires_redis and not requires_api and not requires_celery"` contra
    Redis desechable → 1 passed.
  - `ruff check src` sin hallazgos y `mypy src` → 236 ficheros sin errores.
  - `docker compose config` válido para el overlay de CI y para Grafana.
- La suite contra API/GraphQL/SSO/Jaeger/Grafana live no se ejecutó localmente
  porque incluye limpieza destructiva del grafo Neo4j y servicios adicionales. El
  job está preparado para ejecutarla en un entorno desechable, pero su resultado en
  GitHub Actions debe confirmarse al habilitar el workflow.
- Implementación principal: commit `7b74bdb` (`test(ci): make integration suite
  reproducible (#606)`).
