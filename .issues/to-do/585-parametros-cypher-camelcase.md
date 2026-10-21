# Issue #585: 10 endpoints → 500 por parámetros Cypher mal enlazados (`$projectId` vs `project_id=`, `$agentId` vs `agent_id=`, `$closed_at` ausente)

## Description

Toda una familia de endpoints revienta con `500` porque **la query Cypher pide un
parámetro con un nombre y el caller pasa otro** (o no lo pasa). Neo4j responde
`ClientError: Expected parameter(s): X` y el handler lo deja escapar como
`INTERNAL_ERROR`.

Verificado in-process 2026-10-21 con `app.debug=True` (tracebacks reales) + código:

| Endpoint | Parámetro que pide la query | Quién/cómo la llama |
|---|---|---|
| `GET /policies/project/{id}` | `projectId` (`GET_POLICIES_FOR_PROJECT`, `neo4j_queries.py:1176`) | repo pasa otro nombre → `ParameterMissing: projectId` (traceback vivo) |
| `GET /policies/agent/{id}` | `agentId` (`GET_POLICIES_FOR_AGENT`, `neo4j_queries.py:1183`) | `neo4j_policy_repository.py:175+` → traceback vivo |
| `POST /policies/{id}/link/agent/{agent}` | `$agentId` (`LINK_POLICY_TO_AGENT`, `neo4j_queries.py:1162-1167`) | `neo4j_policy_repository.py:150-153` pasa `agent_id=` (ERR en run4) |
| `POST /policies/{id}/link/component/{comp}` | `$componentId` (`LINK_POLICY_TO_COMPONENT`, `neo4j_queries.py:1169-1174`) | repo pasa `component_id=` (ERR en run4) |
| `GET /agents/{agent_id}/specialists` | `agentId` | `routers/agent.py:480` → traceback vivo |
| `GET /components/{component_id}/specialists` | `componentId` | `routers/agent.py:503` → traceback vivo |
| `POST/DELETE /agents/{id}/specialists/{component_id}` | familia | ERR en run4 |
| `GET /projects/{id}/agents` | `projectId` (`PROJECT_GET_AGENTS`, `neo4j_queries.py:198-202`) | `routers/project.py:589` pasa `project_id=` → ERR en run4 |
| `POST/DELETE /projects/{id}/agents/{agent_id}` | `$projectId`/`$agentId` (`PROJECT_ASSIGN_AGENT`/`PROJECT_REMOVE_AGENT`, `neo4j_queries.py:185-196`) | `routers/project.py:536-540` y `563-567` pasan `project_id=`/`agent_id=` → ERR en run4 |
| `POST /commits/{sha}/link/agent/{agent_id}` | `$agentId` (`LINK_COMMIT_TO_AGENT`, `neo4j_queries.py:1029-1034`) | `neo4j_commit_repository.py:104-108` pasa `agent_id=` (ERR en run4) |

Y una variante del mismo cáncer de "parámetros no alineados":
`POST /issues/{issue_id}/affects` con body string válido e issue real →
`ParameterMissing: Expected parameter(s): closed_at` (reproducido con issue real el
2026-10-21): la query de `add_affects_symbol`
(`neo4j_impl/issue_mixin.py:250+`) exige `$closed_at` y el caller no lo manda.

Los nombres se mezclan **dentro del propio fichero de queries**: `$policy_id` snake
junto a `$agentId` camel (`neo4j_queries.py:1162-1174`) — nunca hubo convención.

Endpoints que sí van bien (control): `GET /policies/component/{id}` → 200,
`POST /policies/{id}/link/project/{project_id}` → 200 (ahí los nombres coinciden).

## Status: OPEN

## Priority: HIGH

## Component
Backend / Neo4j (queries + repositorios + routers)

## Type
bug fix / backend

## Implementation

1. **Auditoría mecánica de parámetros**: para cada query de `neo4j_queries.py`,
   cruzar `$<param>` con los kwargs de sus `session.run(...)` call-sites. Automatizable
   con un grep/regex (o un test que parsee el fichero): el test que fije el
   emparejamiento evita la próxima regresión.
2. **Unificar convención** (decidir una y aplicarla en TODO: queries + callers):
   snake_case (`project_id`, `agent_id`, `component_id`, `closed_at`) — coherente con
   `$policy_id` que ya existe y con los kwargs de Python. Renombrar en
   `neo4j_queries.py` y call-sites afectados (la tabla de arriba es la lista de
   trabajo).
3. **`POST /issues/{id}/affects`**: la query exige `closed_at` → pasar
   `closed_at` (issue cerrada/now) o quitarlo de la query si no aplica; revisar
   también `remove_affects_symbol` (`issue_mixin.py:287+`) por si repite el patrón.
4. **Cobertura de humo**: un test por endpoint de la tabla que con un id inexistente
   espere **404** (o 200 con lista vacía), **no 500** — el contrato mínimo es "nunca
   ParameterMissing".

## Acceptance Criteria
- [ ] Cada endpoint de la tabla → 200/404 con ids inexistentes (ya no 500
      `ParameterMissing`)
- [ ] `POST /issues/{id}/affects` con issue real y body string → 2xx sin
      `ParameterMissing: closed_at` (idem DELETE)
- [ ] Todos los `$params` de `neo4j_queries.py` coinciden con los kwargs de sus
      call-sites (verificado por test o auditoría documentada)
- [ ] Convención de nombres de parámetros única y aplicada (sin `policy_id` +
      `agentId` en el mismo fichero)
- [ ] Gates: ruff/mypy sin delta, pytest sin nuevas fallas

## Files to Modify
- `src/socialseed_tasker/infrastructure/neo4j_queries.py` (185-202, 1029-1034,
  1162-1201, queries de specialists y de affects/closed_at)
- `src/socialseed_tasker/infrastructure/neo4j_policy_repository.py` (147-175)
- `src/socialseed_tasker/infrastructure/neo4j_commit_repository.py` (101-108)
- `src/socialseed_tasker/infrastructure/web_api/routers/project.py` (517-591)
- `src/socialseed_tasker/infrastructure/web_api/routers/agent.py` (426-510)
- `src/socialseed_tasker/infrastructure/neo4j_impl/issue_mixin.py` (250-300)
- `src/socialseed_tasker/infrastructure/web_api/routers/policy_relationships.py`
- `tests/` — tests 404/200 por endpoint

## Related Issues
- #578/#584 (camelCase en atributos de modelo, otra familia de 500), #586 (afecta a
  `manifest/todo`, misma toxina de params), #594 (observabilidad), #588 (el delete de
  policies que ni siquiera llega a Neo4j)

## Notes
- **Repro general**: cualquier endpoint de la tabla con id inventado → 500
  `INTERNAL_ERROR`; con `app.debug=True` se ve
  `neo4j.exceptions.ClientError ... Expected parameter(s): X`.
- La tabla incluye endpoints verificados por traceback y endpoints heredados del
  smoke run4 con causa inferida por el mismo patrón — al implementar, **reproducir
  todos** (docker exec con debug) para no dejar ninguno sin fix real.
