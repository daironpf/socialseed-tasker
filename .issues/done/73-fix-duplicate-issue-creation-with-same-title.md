# 73-fix-duplicate-issue-creation-with-same-title

## Problema identificado
Al crear issues con títulos idénticos en el mismo componente, el sistema permite crear duplicados sin advertencia. Esto genera confusión al intentar gestionar dependencias, ya que al intentar añadir una dependencia en la misma request, el endpoint falla con "Issue not found" porque los IDs de los issues no se devuelven de forma consistente en la respuesta.

## Evidencia
```bash
# Crear dos issues con el mismo título en el mismo componente
ISSUE1=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"Crear base de datos de productos","component_id":"88d5f85b-f0ed-4a3d-a40c-b3d0f2dcb511","priority":"HIGH"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

ISSUE2=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"Crear base de datos de productos","component_id":"88d5f85b-f0ed-4a3d-a40c-b3d0f2dcb511","priority":"HIGH"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Intentar crear dependencia falla con error confuso
curl -s -X POST "http://localhost:8000/api/v1/issues/$ISSUE2/dependencies" \
  -H "Content-Type: application/json" \
  -d "{\"depends_on_id\":\"$ISSUE1\"}"
# Error: "Issue not found" (aunque el issue existe)
```

## Impacto negativo
- Confusión para el agente que intenta crear tareas relacionadas
- Posibilidad de crear múltiples issues duplicados sin notificación
- Dificultad para identificar y gestionar dependencias entre issues

## Propuesta de solución
1. Añadir validación para detectar títulos duplicados en el mismo componente
2. Devolver warning en la respuesta cuando se detecte duplicado
3. Mejorar el mensaje de error al intentar crear dependencia con issue inexistente