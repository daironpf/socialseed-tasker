# Issue #366: `tasker reasoning log` falls con "Database connection failed"

## Description
El comando `tasker reasoning log` falla con el mensaje "Database connection failed: Check that Neo4j is running and accessible" incluso cuando la API reporta estado healthy y Neo4j connected.

## Expected Behavior
El comando debería loguear el razonamiento exitosamente a través de la API REST, usando la conexión configurada en modo API.

## Actual Behavior
El CLI intenta conectarse directamente por Bolt en vez de usar la API REST.

## Steps to Reproduce
1. Asegurar que `tasker status` muestre "Mode: api" y "Connection: connected"
2. Ejecutar: `tasker reasoning log -i <issue-id> -t "test reasoning"`
3. Observar error: "Database connection failed: Check that Neo4j is running and accessible"

## Status: RESOLVED

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Asegurar que el comando `reasoning log` use el modo API (REST) cuando `connection_mode` es "api", en lugar de intentar conexión directa Bolt.

## Impact
Bloquea la capacidad de los agentes de registrar razonamiento, afectando la trazabilidad organizacional.

## Related Issues
- FIND-001 del reporte de prueba
