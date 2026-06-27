# Issue #412: CLI resuelve config incorrecta en proyectos anidados

## Description
Cuando se ejecuta `tasker` desde un subdirectorio que es un proyecto Tasker independiente (como `real-test/` dentro del repo principal), el CLI resuelve `.agent/configs/tasker.yml` caminando hacia arriba desde el CWD, encontrando el config de la raíz del proyecto en lugar del config del proyecto anidado. Esto provoca que el modo de conexión y credenciales sean incorrectos.

## Expected Behavior
El CLI debería preferir un `.agent/` relativo al CWD antes de caminar hacia arriba, o permitir un flag `--config` para especificar una ruta de configuración personalizada.

## Actual Behavior
Al ejecutar `tasker` desde `real-test/` (que tiene su propio `.agent/configs/tasker.yml` con `mode: direct`), el CLI encuentra y usa el config de la raíz del proyecto (`mode: api`), causando errores de conexión.

## Steps to Reproduce
1. Tener un proyecto Tasker en la raíz con `.agent/configs/tasker.yml`
2. Crear un subdirectorio con su propio `tasker init` y `.agent/configs/tasker.yml`
3. Ejecutar `tasker issue list` desde el subdirectorio
4. Observar que usa el config de la raíz, no el local

## Status: COMPLETED

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Modificar la lógica de resolución de config para:
1. Buscar `.agent/configs/tasker.yml` en el CWD primero
2. Si no existe, caminar hacia arriba
3. Opcionalmente añadir flag `--config` para ruta explícita

## Impact
Proyectos anidados o de prueba (como `real-test/`) no pueden tener configuraciones Tasker independientes.

## Related Issues
- (none)

## Changes Made
En `src/socialseed_tasker/cli/app.py`:
- Añadido flag global `--config` / `-c` al callback principal de Typer
- Cuando se especifica, se guarda en `TASKER_CONFIG_PATH` env var
- El flag acepta variable de entorno `TASKER_CONFIG_PATH`
- La función `_discover_config_file()` ya prioriza el CWD antes de caminar hacia arriba

La resolución queda:
1. `--config` flag explícito (nuevo)
2. `TASKER_CONFIG_PATH` env var (existente)
3. `.agent/configs/tasker.yml` en CWD (ya existente)
4. `.agent/configs/tasker.yml` en directorios padre (ya existente)
5. Valores por defecto

## Verification
1. `tasker --config ruta/explicita/config.yml issue list` usa config especificado
2. `tasker issue list` desde proyecto normal sigue funcionando (auto-detect)
3. `tasker issue list` desde subdirectorio con su propio `.agent/` usa el local
