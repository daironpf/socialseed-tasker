# Issue #367: Falta comando CLI `tasker project create`

## Description
No existe un comando CLI para crear proyectos. `tasker project` solo ofrece los subcomandos `detect` y `setup`. Para crear un proyecto hay que usar la API REST directamente.

## Expected Behavior
Debería existir `tasker project create --name <name>` para crear proyectos desde la CLI.

## Actual Behavior
`tasker project --help` solo muestra `detect` y `setup`. No hay forma de crear un proyecto desde CLI.

## Steps to Reproduce
1. Ejecutar: `tasker project --help`
2. Observar que no hay subcomando `create`

## Status: RESOLVED

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Agregar comando `tasker project create --name <name>` que haga POST a `/api/v1/projects`.

## Impact
Los usuarios deben usar curl/API directamente para crear proyectos, lo cual es una fricción UX.

## Related Issues
- FIND-002 del reporte de prueba
