# 74-improve-root-cause-analysis-endpoint-clarity

## Problema identificado
El endpoint `/api/v1/analyze/root-cause` requiere parámetros que no son intuitivos para un agente de IA que llega por primera vez. El endpoint pide `test_id`, `test_name` y `error_message`, lo cual presupone que el agente ya tiene un test fallando, pero un agente nuevo esperando analizar la causa raíz de un issue se encontrará confuso.

## Evidencia
```bash
# Un agente nuevo probaría algo como esto:
curl -s -X POST "http://localhost:8000/api/v1/analyze/root-cause" \
  -H "Content-Type: application/json" \
  -d '{"issue_id":"7eb0880e-8c3e-4bcd-9e2f-b0c069b3dba9"}'

# Error: Field required: test_id, test_name, error_message

# El agente no sabe que necesita ejecutar primero un test para obtener estos datos
```

## Impacto negativo
- Curva de aprendizaje alta para nuevos agentes
- El nombre del endpoint sugiere funcionalidad diferente a la real
- Confusión entre "análisis de causa raíz" y "registro de test fallido"

## Propuesta de solución
1. Renombrar endpoint a `/api/v1/analyze/link-test` o similar para mayor claridad
2. Crear un endpoint `/api/v1/analyze/root-cause/{issue_id}` que solo requiera el issue_id
3. Documentar mejor en el OpenAPI el flujo de uso del análisis