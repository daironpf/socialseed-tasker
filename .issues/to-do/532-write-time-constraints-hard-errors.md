# Issue #532: Validación de políticas en tiempo de escritura + errores HARD explícitos

## Description

El backend ya valida políticas al crear dependencias (`PolicyEngine.validate_dependency` con `enforcement_mode=warn|block` → 409 en `POST /issues/{id}/dependencies`) y detecta ciclos (`CircularDependencyError` → handler 409); `POST /api/v1/constraints/validate` valida el estado y la UI de constraints ya muestra categorías (`ARCHITECTURE`, `TECHNOLOGY`, `NAMING`, `PATTERNS`, `DEPENDENCIES`) y severidades `HARD`/`SOFT` (#10, #84, #126). Faltan dos cosas que pide la ÉPICA 4 de `notas.md`: (1) la **profundidad máxima** (`max_depth`) solo se comprueba en la validación de estado (`_check_max_dependency_depth`), no al crear la dependencia; (2) el frontend no muestra una **notificación explícita** cuando se viola una política `HARD` (el error llega como toast genérico de la capa de cliente).

Origen: `notas.md` → ÉPICA 4 · Issue #10 (→ #532).

## Status: TODO

## Priority: HIGH

## Component
Backend + Frontend / Governance / Constraints

## Type
feat / governance

## Implementation
1. **Interceptor de profundidad:** en `POST /issues/{id}/dependencies` (y bulk), además del `PolicyEngine`, ejecutar la comprobación de la constraint `DEPENDENCIES`/`max_depth` (reutilizar `_check_max_dependency_depth` de `application/constraints.py`) → 409 con `message` + `suggestion` cuando se exceda.
2. **Respuesta estructurada:** aprovechar los `exception_handler` existentes de `PolicyViolationError`/`CircularDependencyError` (`app.py`) para devolver siempre `code`, `message`, `suggestion` y `policy_name`/`constraint` en `detail`.
3. **UX frontend HARD:** `frontend/src/components/ui/RelationshipModal.vue` y el flujo de agregar dependencia muestran el error devuelto (nombre de la política/constraint, severidad HARD, sugerencia) en un panel inline traducido en lugar de un toast genérico.
4. **Tests:** unit de la regla `max_depth` en escritura, test del handler 409 y spec del modal.

## Acceptance Criteria
- [ ] Crear una dependencia que exceda `max_depth` o viole una política en modo `block` aborta la creación con 409 y detalle estructurado
- [ ] El frontend muestra una notificación explícita de la violación HARD (política + sugerencia) al agregar la dependencia
- [ ] Los ciclos siguen respondiendo 409 con mensaje legible
- [ ] i18n support (EN + ES); `npm run build` passes
- [ ] Gates backend sin regresiones

## Files to Create
- `tests/unit/test_max_depth_write_time.py`
- `frontend/src/components/ui/RelationshipModal.spec.ts`

## Files to Modify
- `src/socialseed_tasker/infrastructure/web_api/routers/dependencies.py` — check `max_depth` en add/bulk
- `src/socialseed_tasker/application/constraints.py` — helper reutilizable de profundidad en escritura
- `src/socialseed_tasker/infrastructure/web_api/app.py` — `detail` estructurado (si hace falta)
- `frontend/src/components/ui/RelationshipModal.vue` — error inline HARD
- `frontend/src/locales/en.json` / `es.json`
- `features.md` — §10/§41

## Related Issues
- #84 (Graph policy engine), #82 (Active policy enforcement), #85 (Pre-execution validation), #110 (Dependency validation), #126 (Constraints configuration), #485/#501 (governance UI), #510 (RBAC/HITL UI)
