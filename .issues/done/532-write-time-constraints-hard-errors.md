# Issue #532: Validación de políticas en tiempo de escritura + errores HARD explícitos

## Description

El backend ya valida políticas al crear dependencias (`PolicyEngine.validate_dependency` con `enforcement_mode=warn|block` → 409 en `POST /issues/{id}/dependencies`) y detecta ciclos (`CircularDependencyError` → handler 409); `POST /api/v1/constraints/validate` valida el estado y la UI de constraints ya muestra categorías (`ARCHITECTURE`, `TECHNOLOGY`, `NAMING`, `PATTERNS`, `DEPENDENCIES`) y severidades `HARD`/`SOFT` (#10, #84, #126). Faltan dos cosas que pide la ÉPICA 4 de `notas.md`: (1) la **profundidad máxima** (`max_depth`) solo se comprobaba en la validación de estado (`_check_max_dependency_depth`), no al crear la dependencia; (2) el frontend no mostraba una **notificación explícita** cuando se viola una política `HARD` (el error llegaba como toast genérico de la capa de cliente).

Origen: `notas.md` → ÉPICA 4 · Issue #10 (→ #532).

## Status: DONE (2026-10-01)

## Priority: HIGH

## Component
Backend + Frontend / Governance / Constraints

## Type
feat / governance

## Implementation
1. **Interceptor de profundidad:** `check_max_depth_at_write_time` en `application/actions.py` (junto a `_check_max_dependency_depth`): `new_depth = 1 + depth(depends_on_id)` contra constraints activas `DEPENDENCIES`/`max_depth`; solo `HARD` aborta con `PolicyViolationError` (SOFT/inactivas no bloquean). Aplicado en `POST /issues/{id}/dependencies` (antes de `add_dependency_action`) y pre-check en `.../dependencies/bulk` (aborta la petición completa con 409 antes de crear nada).
2. **Respuesta estructurada:** `PolicyViolationError` gana `constraint` y `severity`; handler en `app.py` responde **409** (antes 400) con el envelope `_error_response` y `details = {policy_name, constraint, rule_type, severity, message, suggestion}`; `CircularDependencyError` sigue en 409 y ahora incluye `details.cycle_path`.
3. **UX frontend HARD:** `client.ts` propaga `code`/`details`/`status` en el Error rechazado y acepta `suppressErrorToast` (las llamadas puntuales pueden pedir panel en vez de toast); `issuesApi.addDependency()` crea la dependencia con esa flag; `GraphView` llama a la API en `onCreateRelationship` (antes solo cerraba el modal), refresca los issues al tener éxito y monta el error en `relError`; `RelationshipModal` renderiza un **panel inline** con título traducido, badge de severidad (HARD/SOFT), mensaje, política/constraint y sugerencia (también para `CIRCULAR_DEPENDENCY`).
4. **Tests:** `tests/unit/test_max_depth_write_time.py` (12) y `frontend/src/components/ui/RelationshipModal.spec.ts` (5).

## Acceptance Criteria
- [x] Crear una dependencia que exceda `max_depth` o viole una política en modo `block` aborta la creación con 409 y detalle estructurado
- [x] El frontend muestra una notificación explícita de la violación HARD (política + sugerencia) al agregar la dependencia
- [x] Los ciclos siguen respondiendo 409 con mensaje legible
- [x] i18n support (EN + ES); `npm run build` passes
- [x] Gates backend sin regresiones

## Verification
- **Gates backend:** `ruff check src/` = 1011 (baseline) ✓ · `mypy src/` = 1151/133 (mejora vs baseline 1154, sin nuevos errores) ✓ · `pytest -q` = **1178 passed / 27 skipped / 3 failed** (solo los 3 preexistentes: `test_delivery_retries`, 2x `test_tasks_unit`) ✓
- **Tests nuevos:** `tests/unit/test_max_depth_write_time.py` 12/12 — helper (lanza con campos estructurados, permite dentro del límite, SOFT/inactiva no bloquean), endpoint (409 con `details` completo + nada persistido, 201 dentro de límite, SOFT/inactiva → 201, bulk → 409, ciclo → 409 con `cycle_path`), política en modo `block` → 409 estructurado y en `warn` → 201 ✓
- **Gates frontend:** `npm run lint` 0 errores (2 warnings preexistentes vue/no-mutating-props) · `npm test` = **208/208** (+5 modal) · `npm run build` (vue-tsc) verde ✓
- **Smoke real** (stack compose, `tasker-api` :8888 reconstruido): **24/24 PASS** — carga de constraint `max_depth=1` (queda ACTIVE), cadena B→C creada (201), C→B → 409 `CIRCULAR_DEPENDENCY` con mensaje legible y `cycle_path`, A→B → 409 `POLICY_VIOLATION` con `rule_type=max_depth`/`severity=hard`/`constraint`/`suggestion` y sin persistir, bulk → 409 sin crear nada; limpieza completa (issues/componente/constraints a 0) ✓
- **Notas (comportamiento y preexistente):** (a) orden de chequeos: `PolicyEngine` → `max_depth` → acción (ciclo/duplicado); si una petición vulnera a la vez profundidad y ciclo, responde `POLICY_VIOLATION` (ambos 409); sin constraints activas los ciclos responden `CIRCULAR_DEPENDENCY` siempre. (b) **Gap preexistente descubierto:** `constraints_router` usa rutas `""` con prefix `/api/v1`, por lo que list/load responden en `GET/POST /api/v1` y **no** en `/api/v1/constraints` (solo `/constraints/validate` está bien montado); fuera de alcance de #532, candidato a #126. (c) `BLOCKS` en el modal sigue sin endpoint backend (solo `DEPENDS_ON` persiste), preexistente.

## Files to Create
- `tests/unit/test_max_depth_write_time.py`
- `frontend/src/components/ui/RelationshipModal.spec.ts`

## Files to Modify
- `src/socialseed_tasker/application/actions.py` — `PolicyViolationError` + `constraint`/`severity`, helper `check_max_depth_at_write_time`
- `src/socialseed_tasker/infrastructure/web_api/routers/dependencies.py` — check `max_depth` en add/bulk + narrowing de `depends_on_id`
- `src/socialseed_tasker/infrastructure/web_api/app.py` — handler `POLICY_VIOLATION` → 409 con `details` completo; `CIRCULAR_DEPENDENCY` con `cycle_path`
- `frontend/src/api/client.ts` — `code`/`details`/`status` en el Error + flag `suppressErrorToast`
- `frontend/src/api/issuesApi.ts` — `addDependency()`
- `frontend/src/types/index.ts` — `PolicyViolationDetail`
- `frontend/src/components/ui/RelationshipModal.vue` — panel inline HARD
- `frontend/src/views/GraphView.vue` — llamada real + `relError` + refresh
- `frontend/src/locales/en.json` / `es.json` — `graph.policyViolation`, `graph.violationConstraint/Policy/Suggestion`
- `features.md` — §10/§12/§41

## Related Issues
- #84 (Graph policy engine), #82 (Active policy enforcement), #85 (Pre-execution validation), #110 (Dependency validation), #126 (Constraints configuration), #485/#501 (governance UI), #510 (RBAC/HITL UI)
