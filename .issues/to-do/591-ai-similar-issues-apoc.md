# Issue #591: `GET /ai/similar-issues/{id}` → 500 — usa `apoc.algo.similarity` y APOC no existe en el Neo4j del stack

## Description

El endpoint de issues similares falla siempre con `500` en el backend real:

```
GET /api/v1/ai/similar-issues/{issue_id} -> 500
  neo4j.exceptions.CypherSyntaxError:
  Unknown function 'apoc.algo.similarity' (line 7, column 13 (offset: 179))
  {gql_status: 50N42}
```

(Verificado in-process 2026-10-21 con `app.debug=True` dentro de `tasker-api`; ERR en
run4.)

**Causa raíz**: la query de similitud invoca la función de APOC
`apoc.algo.similarity(...)`, pero el Neo4j del stack (`neo4j:5.26.15-community`,
contenedor `tasker-db`) **no tiene APOC instalado/habilitado** → la función no existe
→ `CypherSyntaxError` → 500. Neo4j no diferencia "función desconocida por plugin
ausente" de un error de sintaxis, y el handler no lo traduce.

A esto se suma que el 500 llega con el envelope opaco `INTERNAL_ERROR` (ver #594): en
`docker logs tasker-api` no hay rastro de la causa.

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / AI + infra Neo4j (APOC)

## Type
bug fix / backend + infra

## Implementation

Decidir entre dos caminos (o combinarlos):

1. **Opción A — habilitar APOC en el stack** (si se quiere conservar la fórmula):
   - `docker-compose.yml`: montar el plugin APOC en `tasker-db` (la imagen community
     trae `apoc` como plugin descargable) + `NEO4J_PLUGINS='["apoc"]'` y/o
     `apoc.conf` con `apoc.function.similarity...` según la versión (5.26).
   - Verificar en vivo: `cypher-shell ... "RETURN apoc.algo.similarity([1,2],[1,3])"`
     (o la función exacta usada).
2. **Opción B — degradar sin APOC** (más robusta):
   - Detectar disponibilidad una vez (probe `RETURN apoc.algo.similarity` con
     try/except) y, si falta, calcular similitud con funciones nativas (distancia
     sobre embeddings almacenados, matching de etiquetas/títulos) o devolver
     `503 APOC_NOT_AVAILABLE` con mensaje claro — **nunca** 500.
3. En cualquier caso: **mapear errores Cypher de "función desconocida"** a un estado
   controlado en este handler (503/501 con código) — patrón de #589/#590.
4. **Tests**:
   - `test_similar_issues_degrades_without_apoc` (driver fake que lanza
     `CypherSyntaxError` por función desconocida → 503/respuesta degradada, no 500).
   - Si se elige A: test de integración marcado que solo corre con APOC presente.

## Acceptance Criteria
- [ ] `GET /api/v1/ai/similar-issues/{id}` → 200 (con resultados o lista vacía) **o**
      503 con código semántico — ya no 500 `Unknown function`
- [ ] Decisión APOC tomada y reflejada: compose con plugin **o** código sin APOC
- [ ] La ausencia de una función de Cypher nunca se vuelve 500 genérico en este handler
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- La query de similitud (buscar `apoc.algo.similarity` en
  `src/socialseed_tasker/infrastructure/` — queries/repo de AI o RAG)
- El handler de `GET /ai/similar-issues/{id}` (router `ai`)
- `docker-compose.yml` + `tasker-db` (solo si Opción A)
- `tests/api/` — test de degradación

## Related Issues
- #589/#590 (mismo patrón: dependencia externa ausente → 500), #594 (observabilidad),
  #580 (otro 500 de Cypher en el mismo Neo4j), #585 (familia de queries)

## Notes
- **Repro**: `curl http://127.0.0.1:8888/api/v1/ai/similar-issues/{id} -H 'X-API-Key:
  test-token'` → 500.
- Nota de diagnóstico: `POST /ai/backfill-embeddings` estaba en el SKIP del smoke por
  coste — al implementar, revisar si depende también de APOC/abrir el mismo guard.
