# Issue #605: Eliminar los errores de mypy en `src/` sin debilitar el modo estricto

## Description

La revisión general encontró **1.054 errores de mypy en 131 archivos de `src/`**.
`mypy.ini`/`pyproject.toml` mantienen `strict = true`, mientras que hay paquetes con
deuda tipada desigual. Un chequeo posterior del paquete `domain` quedó limpio tras
tipar `_now()`, pero los errores del resto del proyecto siguen siendo deuda pendiente.

El objetivo es eliminar esa deuda global de manera verificable, paquete a paquete, sin
apagar reglas, añadir ignores amplios ni convertir el typecheck de CI en un falso
positivo.

## Status: DONE — 2026-10-27

## Priority: MEDIUM

## Component
Backend / tipado estático (mypy)

## Type
quality / backend

## Implementation

1. Ejecutar `mypy src/` al iniciar y registrar el número de errores y su distribución
   por paquete/módulo. No asumir que el total previo de 1.054 permanece igual después
   de los cambios recientes.
2. Seleccionar un paquete o grupo coherente de módulos con errores localizados y
   corregirlos con tipos precisos, guards y contratos existentes.
3. Mantener el modo estricto global y los gates de CI. No rebajar `strict`, activar
   `ignore_errors` ni añadir `type: ignore` sin una causa técnica estrecha, explicada
   y comprobada; una excepción no sustituye la corrección de un error evitable.
4. Repetir el typecheck global y enfocado al cerrar cada lote. Continuar con lotes
   adicionales hasta que `mypy src/` finalice sin errores.

## Acceptance Criteria
- [x] El conteo global final de `mypy src/` es cero.
- [x] Todos los paquetes/módulos de `src/` pasan el modo estricto del proyecto.
- [x] `strict = true` permanece habilitado y no se introducen ignores globales ni
      excepciones de módulo para enmascarar el backlog.
- [x] El typecheck global y las pruebas pertinentes pasan; la resolución registra
      baseline, conteo final cero, módulos y pruebas ejecutadas.

## Files to Modify
- `src/` — paquetes seleccionados tras medir el baseline vigente
- `pyproject.toml` / `mypy.ini` — solo si se necesita una excepción estrecha y
  justificada; no debilitar el perfil estricto del proyecto

## Related Issues
- #604 (reducción gradual de hallazgos Ruff)
- Revisión general del proyecto: baseline inicial de 1.054 errores de mypy en 131
  archivos y recomendación de migración incremental

## Notes
- El chequeo del paquete `domain` pasó después de añadir la anotación de retorno a
  `_now()`. Mantener ese resultado, pero no extrapolarlo al resto de `src/`.
- El CI existente ejecuta mypy globalmente; esta issue no autoriza a eliminar o
  relajar ese gate.
- La imagen Docker usa Python 3.10 mientras mypy apunta a 3.12: `logging.LoggerAdapter`
  no es subscriptable en 3.10 en tiempo de ejecucion (el venv 3.14 si lo permite).
  Se detecto al arrancar la imagen reconstruida y se corrigio con un alias bajo
  `TYPE_CHECKING`. Pendiente en otra issue: alinear el target de mypy con la imagen
  o subir la base a 3.12.

## Resolution
- Baseline vigente al iniciar sobre el worktree disponible: 256 errores en 82
  archivos con `python -m mypy src/ --python-version 3.12`. El baseline histórico de
  1.054 errores/131 archivos corresponde a la revisión general anterior.
- Resultado final: `python -m mypy src/` pasa con cero errores en 236 archivos.
  `strict = true` permanece habilitado; no se añadieron ignores globales ni de
  módulos para ocultar diagnósticos.
- Se corrigieron los contratos tipados y validaciones en application, auth, CLI,
  config, data catalog/quality, domain, events, graphviz, GraphQL, infraestructura,
  ML, observability, privacy, tenancy y workers. Se añadieron `types-requests` y
  `types-PyYAML` al perfil de desarrollo.
- El target de mypy se sincronizó a Python 3.12, máximo soportado por el proyecto,
  para analizar los stubs actuales de NumPy, que usan la sintaxis `type` de Python
  3.12; strict sigue activo.
- Pruebas focalizadas de auth, CLI, application, data catalog/quality, config, ML,
  tenancy, events, observability, privacy, workers y API: 231 pasaron. El lote
  enfocado de infraestructura reportó 110 pasadas y 16 omitidas.
- Cierre verificado con el venv del proyecto: `mypy 1.20.0` aún reportaba 12
  errores. Se instalaron los stubs `types-requests`/`types-PyYAML` ya declarados en
  `requirements.txt` y se corrigieron 4 puntos reales: `cast` de las respuestas de
  redis 7.4 (`hgetall`/`get` se tipan como `Awaitable[T] | T`), `cast(Any,
  CeleryInstrumentor)` (instrumentación Celery sin stubs) y `cast(Any, graphql_app)`
  en `add_route` (Ariadne es ASGI). Verificación final: `mypy src` → 0 errores,
  `ruff check src` → 0 y pytest **1712 passed / 62 skipped**.
- Verificación de despliegue: imagen `tasker-api:local` reconstruida y healthy con
  Python 3.10, openapi con 237 rutas y smoke de login/issues/projects/code-graph/AI/
  commits correcto. El arranque destapó que `logging.LoggerAdapter[...]` como clase
  base rompe en 3.10; se sustituyó por un alias `TYPE_CHECKING` y se repitieron
  mypy, ruff, la suite completa y el smoke.
