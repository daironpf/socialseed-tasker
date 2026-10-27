# Issue #605: Eliminar los errores de mypy en `src/` sin debilitar el modo estricto

## Description

La revisión general encontró **1.054 errores de mypy en 131 archivos de `src/`**.
`mypy.ini`/`pyproject.toml` mantienen `strict = true`, mientras que hay paquetes con
deuda tipada desigual. Un chequeo posterior del paquete `domain` quedó limpio tras
tipar `_now()`, pero los errores del resto del proyecto siguen siendo deuda pendiente.

El objetivo es eliminar esa deuda global de manera verificable, paquete a paquete, sin
apagar reglas, añadir ignores amplios ni convertir el typecheck de CI en un falso
positivo.

## Status: TODO

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
- [ ] El conteo global final de `mypy src/` es cero.
- [ ] Todos los paquetes/módulos de `src/` pasan el modo estricto del proyecto.
- [ ] `strict = true` permanece habilitado y no se introducen ignores globales ni
      excepciones de módulo para enmascarar el backlog.
- [ ] El typecheck global y las pruebas pertinentes pasan; la resolución registra
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
