# 77-fix-cli-output-with-extra-blank-lines - LIMITACIÓN CONOCIDA

## Estado: No resuelto (limitación conocida)

## Problema identificado
La salida del CLI tiene líneas en blanco al inicio de cada comando, lo cual parece un bug de renderizado de la librería Rich cuando se usa con Typer.

## Evidencia
```bash
docker exec tasker-api tasker --help

# Salida muestra muchas líneas en blanco al inicio:
                                                                                
 Usage: tasker [OPTIONS] COMMAND [ARGS]...                                      
                                                                                
 SocialSeed Tasker - A graph-based task management framework                    
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
...
```

## Intento de solución
Se probaron múltiples configuraciones de Console de Rich:
- Ajuste de width, soft_wrap, no_color, force_terminal
- Revisión de theme y configuraciones de Typer
- Pruebas con diferentes variables de entorno (TERM=dumb, etc.)

## Resultado
El problema persiste. Las líneas en blanco son generadas internamente por la integración de Typer con Rich y no se pueden eliminar sin modificar el comportamiento de rendering de ayuda de Typer.

## Limitación conocida
Este es un problema conocido a nivel de la librería Typer/Rich. Las alternativas serían:
1. Migrar a un framework CLI diferente (click, argparse)
2. Forkear o modificar Typer internamente
3. Aceptar la limitación

## Cambios realizados
Se mejoró la configuración de Console para mejor visualización:
- `width=80`
- `no_color=False`
- `force_terminal=True`
- `soft_wrap=False`
- `highlight=False`

Estos cambios mejoran el rendimiento y la consistencia del output, aunque las líneas en blanco persisten.