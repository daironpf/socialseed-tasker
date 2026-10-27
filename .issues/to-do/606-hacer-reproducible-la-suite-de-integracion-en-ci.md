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

## Status: TODO

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
- [ ] Todos los tests de integración están asociados a prerrequisitos claros y
      verificables; no dependen de servicios locales implícitos.
- [ ] Cada job/selectores de integración provisiona todos sus servicios y ejecuta
      exitosamente su conjunto de pruebas en CI.
- [ ] Los tests unitarios continúan excluyendo la integración externa y pasan sin
      necesitar los servicios del job opt-in; el comando completo
      `pytest -q -k "not integration" --maxfail=1 --disable-warnings` pasa, no solo
      pruebas focalizadas.
- [ ] No se hace obligatoria la suite completa hasta que el job cubra los servicios
      que realmente consume.
- [ ] La documentación de CI indica cómo ejecutar localmente los mismos grupos de
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
  al encontrar un fallo de expectativa en `/auth/me`; después de corregirlo solo se
  ejecutaron pruebas focalizadas. La validación completa debe repetirse.
- No confundir este trabajo con el harness autenticado de #603: son pruebas y
  entornos diferentes.
