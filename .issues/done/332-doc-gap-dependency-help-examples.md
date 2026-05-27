# Issue #332: Dependency commands --help no muestra ejemplos de uso ni cómo obtener IDs

## Description
Los comandos de dependencias (`tasker dependency add`, `tasker dependency chain`) muestran los parámetros requeridos en `--help` pero no incluyen ejemplos de uso ni explican cómo obtener los IDs de issues necesarios. Un usuario tipo Chaos Monkey (que solo usa `--help`) tiene que descubrir por ensayo y error que `tasker issue list` proporciona los UUIDs.

## Expected Behavior
`tasker dependency add --help` debería incluir:
1. Un ejemplo completo: `tasker dependency add <ISSUE_ID> --depends-on <DEP_ID>`
2. Una nota indicando cómo obtener IDs: "Use `tasker issue list` para ver los IDs disponibles"
3. Referencia cruzada al comando `tasker issue list`

## Actual Behavior
```
$ tasker dependency add --help
Usage: tasker dependency add [OPTIONS] ISSUE_ID
  ...
```
Sin ejemplos ni referencias a cómo obtener ISSUE_ID.

## Steps to Reproduce
1. Ejecutar `tasker dependency add --help`
2. Observar que no hay ejemplos ni indicación de cómo obtener IDs

## Status: PENDING

## Priority: LOW

## Component
CLI — `src/socialseed_tasker/cli/commands/` (dependency command)

## Suggested Fix
Añadir sección de ejemplos en el help text del comando `dependency add` y referencias a `tasker issue list`. Ejemplo:
```
Examples:
  tasker dependency add abc-123 --depends-on xyz-456
  tasker dependency chain abc-123

Note: Use 'tasker issue list' to find issue IDs.
```

## Impact
Mejora la experiencia de desarrolladores nuevos y usuarios Chaos Monkey que dependen exclusivamente de `--help` para navegar el CLI.
