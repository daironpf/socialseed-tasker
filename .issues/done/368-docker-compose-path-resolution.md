# Issue #368: Docker compose path resolution duplicado

## Description
Cuando `tasker init` inicia docker compose con `--profile api`, el path del Dockerfile se resuelve incorrectamente. Busca `.agent/.agent/tasker/Dockerfile` debido a que el `docker-compose.yml` está en `.agent/tasker/` con `context: ..` y `dockerfile: .agent/tasker/Dockerfile`, causando duplicación.

## Expected Behavior
Docker compose debería construirse correctamente desde cualquier directorio.

## Actual Behavior
Error: `resolve: GetFileAttributesEx .agent\.agent: El sistema no puede encontrar el archivo especificado.`

## Steps to Reproduce
1. Ejecutar `tasker init . --force` en modo API
2. El init intenta arrancar docker compose automáticamente
3. Falla con path duplicado

## Workaround
Ejecutar manualmente: `docker compose --profile api up -d --build` desde la raíz del proyecto.

## Status: RESOLVED

## Priority: HIGH

## Component
DOCKER

## Suggested Fix
Corregir el scaffolding del `docker-compose.yml` para que use paths absolutos o relativos correctos desde la raíz del proyecto. Alternativamente, que `tasker init` ejecute docker compose desde el directorio raíz.

## Impact
Los usuarios nuevos no pueden completar `tasker init` sin intervención manual.

## Related Issues
- FIND-003 del reporte de prueba
