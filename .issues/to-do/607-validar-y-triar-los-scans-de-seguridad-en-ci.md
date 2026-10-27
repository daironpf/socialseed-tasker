# Issue #607: Validar los scans de seguridad bloqueantes y triar su baseline

## Description

La revisión encontró que varios workflows suprimían el resultado de los scans con
`|| true`, por lo que los hallazgos no podían bloquear CI. Los cambios propuestos en
`.github/workflows/security-scan.yml` y `.github/workflows/pipeline.yml` reemplazan
Safety por `pip-audit` y retiran la supresión, pero `.github/workflows/dependency-update.yml`
todavía ejecuta `pip-audit || true`. El entorno local de revisión tampoco tenía Bandit
instalado y no se ejecutó ninguno de esos scans contra el baseline real.

Antes de considerar cerrado el control, hay que comprobar que ambos jobs instalan y
ejecutan los scanners, revisar los hallazgos reales y resolverlos de forma explícita,
sin volver a introducir un resultado siempre exitoso.

## Status: TODO

## Priority: HIGH

## Component
CI / seguridad de dependencias y análisis estático

## Type
security / quality

## Implementation

1. Revisar todos los workflows que ejecutan análisis de seguridad, incluidos
   `.github/workflows/security-scan.yml`, `pipeline.yml` y
   `dependency-update.yml`; usar comandos compatibles y eliminar supresiones de exit
   code.
2. Ejecutar `pip-audit --skip-editable` sobre las dependencias instaladas por cada
   workflow y `bandit -r src -lll`; verificar que fallos de instalación o hallazgos
   producen un resultado de job fallido.
3. Clasificar hallazgos por paquete, severidad y alcanzabilidad; corregir toda
   vulnerabilidad confirmada. Solo falsos positivos demostrados pueden exceptuarse,
   con evidencia y alcance mínimo; no dejar vulnerabilidades conocidas como deuda
   aceptada para cerrar la issue.
4. Ejecutar los jobs en GitHub Actions y guardar en la resolución el enlace o resumen
   de resultados y la disposición de cada hallazgo.

## Acceptance Criteria
- [ ] Todos los workflows que ejecutan scans de seguridad están inventariados;
      `pip-audit` ya no se silencia en `dependency-update.yml`.
- [ ] `pip-audit --skip-editable` y `bandit -r src -lll` se ejecutan en los workflows
      de seguridad pertinentes.
- [ ] Un fallo de instalación o un hallazgo del scanner produce fallo real del job;
      no hay supresión global del exit code.
- [ ] Todas las vulnerabilidades confirmadas del baseline se corrigen; solo falsos
      positivos demostrados quedan documentados con evidencia, sin ignorar categorías
      completas.
- [ ] CI confirma que ambos workflows procesan el código/dependencias del commit y
      que no dependen de una herramienta ausente o de un comando obsoleto.

## Files to Modify
- `.github/workflows/security-scan.yml`
- `.github/workflows/pipeline.yml`
- `.github/workflows/dependency-update.yml`
- Dependencias reportadas por `pip-audit`, solo si se confirma actualización segura
- Código señalado por Bandit, solo cuando el hallazgo se verifique

## Related Issues
- #604 (reducción de hallazgos Ruff, gate de calidad general)
- Revisión general del proyecto: scans no bloqueantes y falta de Bandit en el entorno
  local de validación

## Notes
- Los cambios de workflow ya están presentes en el árbol de trabajo, pero no se han
  validado contra Actions ni contra un baseline real de Bandit/pip-audit.
- La inspección posterior encontró `pip-audit || true` en
  `.github/workflows/dependency-update.yml`; también debe quedar cubierto.
