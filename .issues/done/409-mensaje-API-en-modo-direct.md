# Issue #409: Mensaje "Waiting for Tasker API" aparece en modo Direct

## Description
Cuando se ejecuta `tasker init` en modo Direct (conexión directa a Neo4j vía Bolt), el CLI muestra el mensaje "Waiting for Tasker API to be ready to push configuration..." aunque no se necesita ninguna API. Esto causa confusión y un timeout innecesario durante la configuración.

## Expected Behavior
En modo Direct, el init no debe esperar por una API REST. Debería verificar solo la conexión a Neo4j y proceder inmediatamente.

## Actual Behavior
El mensaje "Waiting for Tasker API to be ready to push configuration..." aparece y el proceso se queda esperando hasta timeout, a pesar de que el modo configurado es `direct`.

## Steps to Reproduce
1. Ejecutar `tasker install .` en un proyecto limpio
2. Ejecutar `tasker init` seleccionando modo Direct (opción 1 por defecto)
3. Observar que tras iniciar el contenedor Neo4j, el proceso muestra "Waiting for Tasker API to be ready..."
4. El proceso espera hasta timeout aunque Neo4j ya está healthy

## Status: COMPLETED

## Priority: LOW

## Component
CLI

## Suggested Fix
Revisar el modo de conexión antes de mostrar el mensaje de espera del API. Si el modo es `direct`, saltar la verificación de la API REST y pasar directamente a la configuración final.

## Impact
Confunde a los usuarios durante el setup y hace pensar que hay un problema cuando en realidad el sistema ya está listo.

## Related Issues
- (none)

## Changes Made
En `src/socialseed_tasker/cli/init_command.py:408`, se añadió un bloque condicional `if cli_mode == "direct":` después de arrancar Docker Compose. En modo Direct, se imprime un mensaje de éxito y se retorna temprano, saltando toda la lógica de espera del API REST (health check, creación de proyecto, componentes, policies, etc.) que solo es relevante en modo API.

## Verification
1. Ejecutar `tasker init` en modo Direct
2. Verificar que el mensaje "Waiting for Tasker API to be ready" ya no aparece
3. Verificar que el proceso termina rápidamente con "SUCCESS: TASKER is successfully started and ready!"
4. Verificar que Neo4j sigue funcionando y los comandos tasker funcionan
