# Issue #587: `GET /projects/all` y `GET /projects/current` → 400 — `ProjectResponse` valida `slug=None` y `createdAt` no serializado

## Description

Los dos endpoints "de entrada" de proyectos responden `400 VALIDATION_ERROR` en el
backend real — la API de proyectos entera queda inutilizable desde la UI/clientes:

```
GET /api/v1/projects/all     -> 400
GET /api/v1/projects/current -> 400

{"error":{"code":"VALIDATION_ERROR",
 "message":"2 validation errors for ProjectResponse
   slug: Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
   <segundo error> ..."}}
```

(Verificado in-process 2026-10-21 con `app.debug=True`; en run4 ambos eran los únicos
`4XX` inesperados del bloque de proyectos.)

**Causa raíz** (triage run4 + repro): los nodos `Project` de Neo4j llegan al router con:

1. `slug = None` — el proyecto (creado por setup/seed) **no tiene `slug`** en el grafo,
   pero `ProjectResponse.slug` es `str` obligatorio sin default → Pydantic lanza al
   construir la respuesta; y
2. `createdAt` como `neo4j.time.DateTime` (objeto del driver) en lugar de
   `datetime`/ISO — el segundo de los dos errores de validación.

O sea: falta **normalización en el mapper de proyecto → respuesta** (y de paso, el
proyecto debería nacer con slug o con un fallback). Mientras tanto cualquier lectura
del listado cae entera (un solo nodo malo hunde la respuesta 200 → 400).

## Status: OPEN

## Priority: MEDIUM

## Component
Backend / API (proyectos: mapper y/o schemas)

## Type
bug fix / backend

## Implementation

1. **Mapper** (localizar dónde se construye `ProjectResponse` desde el nodo — router
   `project.py` / repo de proyectos):
   - `createdAt`/`updatedAt`: convertir `neo4j.time.DateTime` → `datetime` (`.to_native()`
     del driver o `datetime(...)`) antes de validar; nunca pasar objetos del driver a
     Pydantic.
   - `slug`: decidir contrato —
     - a) `slug: str | None = None` en `ProjectResponse` (si el dominio admite proyecto
       sin slug), o
     - b) fallback de serialización: `slug or slugify(name)` (o `id`) para que la
       respuesta nunca tenga `None`, o
     - c) garantizar el dato: crear siempre el nodo con `slug` (revisar el alta —
       setup/`create_project`).
     Recomendado: (c) + (b) como red de seguridad (dato correcto + respuesta nunca rota).
2. **No hundir listados**: si algún nodo sigue viniendo corrupto, sanitizar por
   elemento (skip/log) en lugar de que Pydantic reviente la respuesta completa —
   o al menos que el 400 enumere qué nodo falló.
3. **Tests**:
   - `test_projects_all_returns_200_even_without_slug` (nodo sin slug → 200).
   - `test_projects_current_serializes_datetime` (createdAt DateTime del driver → 200
     con ISO).
   - Test con el shape real del nodo (fixture con `neo4j.time.DateTime`).

## Acceptance Criteria
- [ ] `GET /api/v1/projects/all` → 200 con la lista de proyectos (hoy 400)
- [ ] `GET /api/v1/projects/current` → 200 con el proyecto activo
- [ ] `ProjectResponse` no recibe `None` en `slug` ni tipos del driver en fechas
      (o el schema lo admite y lo documenta)
- [ ] Un nodo proyecto mal formado no tumba el listado completo
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/project.py` (construcción de
  `ProjectResponse` en `all`/`current`)
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` (`ProjectResponse`: slug,
  fechas) — si se elige el contrato opcional
- El alta de proyecto (setup/seed) si se elige garantizar `slug`
- `tests/api/` — tests de listado de proyectos

## Related Issues
- #594 (los 400 sí dejan envelope pero los 500 no dejaban logs), #595 (OpenAPI de
  proyectos), #578 (familia de "respostas que Pydantic rechaza")

## Notes
- **Repro**: `curl http://127.0.0.1:8888/api/v1/projects/all -H 'X-API-Key:
  test-token'` → 400 con los 2 errores de `ProjectResponse`.
- El segundo error de validación del mensaje viene truncado en el envelope — en la
  repro con debug se confirma el par (`slug` + `createdAt`); al implementar, mirar el
  traceback completo con `app.debug=True` para no parchear solo el primero.
