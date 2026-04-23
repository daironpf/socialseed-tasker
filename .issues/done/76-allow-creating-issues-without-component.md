# 76-allow-creating-issues-without-component

## Problema identificado
El sistema requiere que todo issue tenga un component_id, pero esto es restrictivo para un agente nuevo que aún está planificando y quiere crear issues de tipo "Idea" o "Backlog" sin saber aún a qué componente pertenecerán.

## Evidencia
```bash
# Intentar crear issue sin componente:
curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"Investigar opciones de pago","priority":"LOW"}'

# Error: Field required: component_id

# El agente no puede crear tareas de planificación de alto nivel
```

## Impacto negativo
- El agente no puede crear issues de backlog sin asignar componente
- Rigidez en el flujo de trabajo del agente
- No permite crear issues "sin asignar" o "por definir"

## Propuesta de solución
1. Hacer component_id opcional en la creación de issues
2. Crear un componente por defecto "uncategorized" o "backlog"
3. Permitir que los issues se muevan a componentes más tarde