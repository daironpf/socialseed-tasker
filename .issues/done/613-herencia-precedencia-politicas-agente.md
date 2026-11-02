# Issue #613: Aplicar herencia y precedencia de políticas al agente

## Description

Un perfil no puede ampliar permisos concedidos por políticas de organización o
proyecto. La autorización efectiva debe combinar esas políticas con el estado y
las restricciones del perfil, y la interfaz debe poder distinguir valores
heredados de valores definidos expresamente. Si no se puede evaluar una política,
el sistema no debe tratarla como permiso.

Completar **AGENT-02** según
`docs/domain-definitions/users/agents_user_definition.md`. Esta issue define la
precedencia y el resultado efectivo; la comprobación en cada acción se aborda en
#615.

## Status: DONE

## Priority: HIGH

## Component
Backend / políticas / usuarios-agente

## Type
feat / backend

## Implementation

1. Implementar la composición de restricciones de organización, proyecto y
   perfil para capacidades, herramientas y alcance de recursos.
2. Representar por separado los valores explícitos y heredados en las respuestas
   de la API.
3. Definir errores y comportamiento seguro cuando una política o su fuente no
   esté disponible o no pueda evaluarse.
4. Cubrir la precedencia con pruebas unitarias y de API.

## Acceptance Criteria
- [x] Las concesiones efectivas son la intersección de las políticas aplicables
      y las restricciones del perfil.
- [x] Una política superior que prohíbe una acción no puede ser sobreescrita por
      el perfil.
- [x] Los valores heredados se distinguen de los valores configurados
      explícitamente.
- [x] Una política desconocida o imposible de evaluar no concede acceso.
- [x] Pruebas verifican tanto la precedencia como los errores de evaluación.

## Files to Modify
- `src/socialseed_tasker/` — servicios de política, permisos y API de agentes
- Pruebas de composición y evaluación de políticas
- Documentación del contrato de usuarios-agente

## Related Issues
- #612 (contrato explícito de permisos)
- #82 (enforcement de políticas activas)
- #84 (motor de políticas del grafo)

## Notes
- Requisito de referencia: **AGENT-02**.
- No inferir permisos por especialización, instrucciones de prompt o presencia
  de controles en la interfaz.

## Resolution

- Dominio puro en `domain/agent_policy.py`: `PermissionSet`,
  `PermissionLimits`, `PolicySource`, `EffectivePermissions` y
  `resolve_effective_permissions()`. Las políticas de organización y proyecto
  son techos: el resultado efectivo es el conjunto explícito del perfil
  intersectado con cada política activa aplicable. Un perfil nunca amplía una
  política superior.
- Tres estados explícitos por capacidad: `None` significa silencio (sin
  restricción heredada), `[]` deniega y una lista concede solo esos valores.
  `inherited` expone el techo combinado, `explicit` el perfil e `effective` la
  intersección final. `None` en el perfil explícito se normaliza a vacío, por lo
  que no concede nada.
- Fail-closed: si una política activa contiene tools o recursos desconocidos, o
  el perfil está deshabilitado, `status` pasa a `unresolved` (o el efectivo queda
  vacío) y `errors` usa códigos seguros `policy:<id>:resource:<scope>` /
  `policy:<id>:tool:<slug>`. Las políticas inactivas se ignoran. La falta de la
  fuente de políticas se mapea a `503`, nunca a una concesión.
- Persistencia: tabla PostgreSQL `agent_permission_policies` con `scope_type`
  restringido a `organization|project`, capacidades JSONB anulables e índice
  `ix_agent_permission_policies_scope`. `PostgresAgentPermissionPolicyStore`
  valida scopes/tools antes de escribir y ofrece `list_for_context()` solo para
  políticas activas del contexto.
- API en `agent_profiles`: `GET/POST /agents/permission-policies`,
  `DELETE /agents/permission-policies/{policy_id}` y
  `GET /agents/profiles/{agent_id}/permissions?organization_id=&project_id=`.
  Los errores de scope/tool se mapean a `422` y los fallos de PostgreSQL a
  `503`. La respuesta separa `explicit`, `inherited`, `effective`, `sources` y
  `errors`; el contexto org/project viaja por query string, sin columnas nuevas
  en el perfil.
- Documentación: contrato de herencia y ejemplos en `docs/API_REFERENCE.md`;
  AGENT-02 y la tabla de estado de
  `docs/domain-definitions/users/agents_user_definition.md` actualizados. El
  enforcement por acción sigue en AGENT-04/#615.
- Pruebas: `tests/unit/test_agent_policy.py` (15) cubre intersección,
  precedencia, silencio/denegación, perfil deshabilitado, políticas inactivas,
  invalidación y normalización; `tests/api/test_agent_policies_api.py` (12)
  cubre permisos efectivos, CRUD, filtros, `404`, `422` y `503`. Se verificó
  además el store real contra PostgreSQL (crear/listar/contexto/borrar) y la
  migración en `tests/api/test_user_schema_migration.py`.
- Evidencia: `ruff` sin hallazgos; `mypy` 238 archivos OK; `pytest -q -k "not
  integration"` 1758 passed, 66 deselected.
