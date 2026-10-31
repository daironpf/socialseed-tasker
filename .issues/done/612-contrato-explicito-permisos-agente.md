# Issue #612: Definir un contrato explícito de permisos para agentes

## Description

El perfil de agente y las opciones de la interfaz no deben confundir propósito,
permisos declarados y autorización efectiva. El contrato actual contempla
`write_access`, pero no representa por separado lectura, propuesta de cambios,
aplicación y ejecución de herramientas. Sin esa distinción, valores ausentes,
listas vacías o referencias inválidas pueden interpretarse de forma demasiado
amplia.

Completar **AGENT-01** según
`docs/domain-definitions/users/agents_user_definition.md`, preservando la
compatibilidad de perfiles existentes sin concederles permisos implícitos.

## Status: DONE — 2026-10-30

## Priority: HIGH

## Component
Backend / usuarios-agente / contrato y persistencia

## Type
feat / backend

## Implementation

1. Definir en los esquemas y el almacenamiento los permisos de lectura,
   propuesta, aplicación y herramientas como capacidades separadas.
2. Especificar la semántica de valores explícitos, heredados, ausentes y vacíos,
   incluyendo el tratamiento de herramientas y recursos desconocidos.
3. Actualizar creación, consulta y edición del perfil y la documentación de la
   API sin almacenar credenciales del proveedor en el perfil.
4. Mantener compatibilidad con los perfiles existentes mediante una migración o
   una interpretación explícita y segura de sus campos actuales.

## Acceptance Criteria
- [x] Lectura, propuesta, aplicación y uso de herramientas tienen semánticas
      distinguibles en el contrato y la persistencia.
- [x] Una lista ausente o vacía no concede acceso; referencias desconocidas o
      inválidas se rechazan con un error explícito.
- [x] `write_access` no concede por sí solo ejecución de comandos, publicación,
      push, borrado ni otras acciones con efectos secundarios.
- [x] No se ofrecen consultas Cypher arbitrarias ni permisos amplios a la base
      de datos como sustituto de capacidades de dominio acotadas.
- [x] Pruebas cubren valores válidos, inválidos, ausentes y vacíos, incluidos
      perfiles existentes.

## Files to Modify
- `src/socialseed_tasker/` — modelos, esquemas, persistencia y API de perfiles
- `docs/API_REFERENCE.md` o documentación vigente del contrato de agentes
- Pruebas de API, modelo y persistencia de perfiles

## Related Issues
- #564 (CRUD de perfiles de agente en PostgreSQL)
- #572 (catálogos de skills y tools)
- #577 (asignación de skills a agentes)

## Notes
- Requisito de referencia: **AGENT-01**.
- Una capacidad presente como dato no demuestra que esté autorizada durante la
  ejecución; el enforcement se cubre en #615.

## Resolution

- Nuevo contrato explícito en `domain/agent_permissions.py`: catálogo acotado
  de recursos (`repository`, `documentation`, `tests`, `issues`, `workflows`,
  `graph`, `configuration`) y normalización que colapsa duplicados y rechaza
  valores vacíos o desconocidos.
- `agents_user` incorpora `read_access`, `propose_access` y `apply_access`
  (JSONB, default `[]`) con migración idempotente
  `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`; las filas existentes conservan
  `write_access` y quedan sin capacidades nuevas.
- `AgentProfileCreate`, `AgentProfileUpdate` y `AgentProfileResponse` exponen
  los campos por separado. En creación, ausente/`[]` no concede acceso; en
  actualización, ausente/`null` conserva y `[]` limpia. `tools` sigue validándose
  contra el catálogo y es una capacidad independiente.
- `write_access` se mantiene por compatibilidad como alcance heredado opaco: no
  se traduce a lectura, propuesta, aplicación ni ejecución de herramientas.
  No se añadieron permisos de base de datos/Cypher; las acciones de dominio se
  solicitan mediante herramientas del catálogo.
- El router mapea `resource:<scope>` a `422 unknown resource` (además del
  `422 unknown tool` existente). Las credenciales del proveedor no forman parte
  del perfil.
- Documentación: `docs/API_REFERENCE.md` (contrato, campos, semántica y errores)
  y `docs/domain-definitions/users/agents_user_definition.md` (AGENT-01 y tabla
  de estado). El enforcement por acción sigue pendiente en AGENT-04/#615.
- Pruebas: `tests/api/test_agent_profiles_api.py` cubre valores válidos,
  inválidos, ausentes, vacíos, duplicados, `write_access` aislado y perfiles
  legacy; `tests/api/test_user_schema_migration.py` verifica la migración.
- Evidencia completa: `ruff` y `mypy` sin hallazgos, `pytest -k "not
  integration"` 1731 passed (66 deseleccionados), frontend 486 tests, lint y
  build con `Bundle guard OK`.
