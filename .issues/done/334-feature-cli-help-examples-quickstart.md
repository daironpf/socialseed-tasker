# Issue #334: Añadir ejemplos rápidos en la salida de tasker --help

## Description
`tasker --help` lista todos los comandos disponibles pero no incluye ejemplos de uso rápido. Un usuario Chaos Monkey que solo usa `--help` como guía no tiene forma de saber la sintaxis exacta sin probar cada comando individual con `--help`.

## Expected Behavior
`tasker --help` debería incluir una sección de ejemplos al final:
```
Examples:
  tasker issue create "Mi titulo" --priority HIGH
  tasker component create "auth-service" -p "my-project"
  tasker dependency add <id> --depends-on <other-id>
  tasker issue list --status OPEN
```

## Actual Behavior
`tasker --help` solo lista comandos y opciones globales, sin ejemplos de uso.

## Steps to Reproduce
1. Ejecutar `tasker --help`
2. Observar que no hay sección de ejemplos ni quick-start

## Status: PENDING

## Priority: MEDIUM

## Component
CLI — `src/socialseed_tasker/cli/app.py` (Typer app definition)

## Suggested Fix
Añadir bloque `Examples:` al final del help del CLI principal usando el parámetro `epilog` de Typer:
```python
app = typer.Typer(
    name="tasker",
    help="...",
    epilog="""
Examples:
  tasker issue create "My title" --priority HIGH
  tasker component list
  tasker dependency add <id> --depends-on <dep_id>
  tasker issue close <id>
"""
)
```

## Impact
Mejora significativamente la experiencia de nuevos usuarios y reduce la fricción de descubrimiento del CLI. Puntuación Chaos Monkey estimada: pasaría de 7/10 a 9/10.
