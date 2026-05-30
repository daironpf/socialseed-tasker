# Issue #369: POST /api/v1/projects retorna validación incorrecta

## Description
Al hacer `POST /api/v1/projects` con un body JSON válido `{"name": "test", "description": "test"}`, la API retorna error de validación esperando campos de issue (title, component_id, priority), lo que sugiere que el endpoint no existe o está mal enrutado.

## Expected Behavior
Debería crear un proyecto y retornar 201 Created con los datos del proyecto.

## Actual Behavior
Retorna 422 con: `Ensure JSON is valid and contains required fields (title, component_id, priority)`

## Steps to Reproduce
1. Ejecutar: `curl -X POST http://localhost:8888/api/v1/projects -H "Content-Type: application/json" -d '{"name":"test","description":"test"}'`
2. Observar error 422 con validación de issues

## Status: RESOLVED

## Priority: LOW

## Component
API

## Suggested Fix
Implementar endpoint `POST /api/v1/projects` o eliminar la ruta si no está implementada para evitar confusión.

## Impact
Bajo, porque se pueden usar proyectos existentes. Pero causa confusión al desarrollar.

## Related Issues
- FIND-004 del reporte de prueba
