# Issue #615: Autorizar cada acción del agente en el backend

## Description

Guardar permisos en un perfil o esconder controles en la UI no protege las
operaciones. Cada herramienta debe validar en el servidor la autorización
efectiva, la capacidad concreta y el alcance del recurso justo antes de ejecutar
la acción. Proponer un cambio tampoco equivale a tener permiso para aplicarlo.

Completar **AGENT-04** según
`docs/domain-definitions/users/agents_user_definition.md`. La UI mock de
gobernanza existente no constituye evidencia de enforcement backend.

## Status: DONE

## Priority: HIGH

## Component
Backend / ejecución de agentes / autorización

## Type
feat / backend

## Implementation

1. Identificar las rutas de ejecución y herramientas que pueden leer o modificar
   recursos.
2. Incorporar una decisión de autorización común que consulte las políticas y
   el contrato de permisos, sin confiar en permisos enviados por el cliente.
3. Validar en cada invocación la identidad y estado del agente, la herramienta,
   la acción y el alcance del recurso.
4. Separar propuesta de aplicación y registrar decisiones permitidas o
   denegadas con un motivo seguro.

## Acceptance Criteria
- [x] Toda acción del agente que accede o modifica recursos valida autorización
      en backend al momento de ejecutarse.
- [x] Acciones fuera de alcance, herramientas desconocidas y agentes
      deshabilitados se deniegan sin efectos secundarios.
- [x] Proponer un cambio no otorga permiso para aplicarlo.
- [x] Un cambio de política se aplica en las validaciones posteriores, incluidas
      las ejecuciones en curso.
- [x] Pruebas cubren acciones permitidas y denegadas, recursos fuera de alcance,
      perfiles deshabilitados y políticas actualizadas.

## Files to Modify
- `src/socialseed_tasker/` — ejecución, catálogo de herramientas y servicios de
  autorización
- Pruebas de autorización por herramienta y recurso
- Documentación de las rutas de acción de agentes

## Related Issues
- #612 (contrato explícito de permisos)
- #613 (herencia y precedencia de políticas)
- #82 (enforcement de políticas activas)
- #85 (validación previa a la ejecución)
- #510 (UI mock de gobernanza y aprobación)

## Notes
- Requisito de referencia: **AGENT-04**.
- La autorización se aplica fuera del prompt y no depende de la visibilidad de
  botones en el frontend.
- El inicio del run emite `X-Agent-Execution-Token`, firmado y ligado al agente,
  run, issue y proyecto; el token solo autentica llamadas MCP y se revoca al
  cerrar el run o al vencer.
- El alcance de proyecto se resuelve desde Project nodes del backend. Mientras
  no exista una relación confiable proyecto-organización, una política
  organizacional activa causa denegación cerrada.
- Las herramientas MCP actuales son de lectura. Las futuras herramientas de
  propuesta/aplicación deben llamar el mismo authorizer con su capacidad
  independiente antes de ejecutar cambios.
