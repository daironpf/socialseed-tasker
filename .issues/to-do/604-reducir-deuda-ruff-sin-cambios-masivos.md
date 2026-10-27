# Issue #604: Eliminar los hallazgos de Ruff en `src/`

## Description

La revisión del proyecto encontró **986 hallazgos de Ruff en `src/`**, incluidos
**7 `F821`** por nombres indefinidos. La tanda de correcciones posterior resolvió
varios casos confirmados en CLI, wiring, routers y el parser, pero no es una limpieza
completa del baseline: queda deuda en varias reglas y módulos.

El objetivo es eliminar todos los hallazgos bajo la configuración Ruff vigente para
`src/`, en lotes revisables, sin esconder el baseline con ignores ni cambiar el
comportamiento del proyecto.

## Status: TODO

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
- [ ] `ruff check src/` termina con cero hallazgos bajo las reglas configuradas.
- [ ] `ruff check src/ --select F821` termina con cero hallazgos.
- [ ] Las pruebas enfocadas de todos los módulos modificados pasan.
- [ ] No se añaden ignores globales, no se deshabilitan reglas y no se introduce
      reformateo ajeno a la corrección.
- [ ] La resolución registra baseline, total final cero, comandos y pruebas ejecutadas.

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
