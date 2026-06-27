# Issue #333: Puerto de API no es obvio desde el CLI (8000 vs 8888)

## Description
El servidor API en Docker se expone en el puerto **8888** (mapeado en docker-compose.yml), mientras que la configuración por defecto y la documentación tradicional mencionan el puerto **8000**. Aunque `tasker init` configura correctamente la URL en `tasker.yml`, un usuario que no haya ejecutado `init` o que use el CLI directamente no tiene forma obvia de saber a qué puerto apunta.

## Expected Behavior
1. `tasker status` debería mostrar la URL activa del API de forma prominente
2. `tasker --help` o `tasker status` debería indicar: "API: http://localhost:8888 (configurado en .agent/configs/tasker.yml)"

## Actual Behavior
- `tasker status` muestra configuración general pero no destaca la URL del API
- La diferencia entre 8000 (default en código) y 8888 (Docker) no es evidente
- `tasker --help` no muestra la URL activa

## Steps to Reproduce
1. Ejecutar `docker compose --profile api up -d`
2. Ejecutar `tasker status`
3. Observar que no hay indicación clara del puerto activo del API

## Status: PENDING

## Priority: LOW

## Component
CLI — `src/socialseed_tasker/cli/commands/status` y `src/socialseed_tasker/config/`

## Suggested Fix
Añadir línea visible en `tasker status`:
```
API URL:    http://localhost:8888  (mode: api)
Neo4j:      bolt://localhost:7687  (connected)
```

## Impact
Mejora la descubribilidad del sistema, especialmente para nuevos usuarios y entornos donde coexisten múltiples configuraciones de puerto.
