# Issue #411: tasker login usa --password mientras el CLI global usa -pw

## Description
El CLI global de tasker usa `--neo4j-password` o `-pw` para especificar la contraseña de Neo4j, pero el subcomando `tasker login` usa `--password` sin una forma corta. Esta inconsistencia en los nombres de parámetros entre subcomandos crea confusión.

## Expected Behavior
El flag de contraseña en `tasker login` debería aceptar los mismos alias que el CLI global (`--neo4j-password`, `-pw`) o al menos tener un alias corto documentado.

## Actual Behavior
`tasker login --help` muestra solo `--password` como opción. No hay alias `-pw` ni `--neo4j-password`. Al intentar `tasker login -pw neoSocial` falla con "Missing parameter: password".

## Steps to Reproduce
1. Ejecutar `tasker -pw neoSocial login`
2. Observar el error "Missing parameter: password"
3. Ejecutar `tasker login --password neoSocial` (funciona correctamente)

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Añadir `-pw` como alias de `--password` en el subcomando `login`, y/o aceptar también `--neo4j-password` para mantener consistencia con el CLI global.

## Impact
Ruptura de la consistencia UX. Usuarios que se acostumbran a usar `-pw` en todos los comandos se encuentran con que `login` no lo acepta.

## Related Issues
- (none)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
