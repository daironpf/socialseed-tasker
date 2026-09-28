# Issue #521: Policy Sandbox Rules Engine

## Description

La vista `PolicySandboxView` genera reportes de impacto predefinidos sintéticamente (`sandboxStore` con fixtures). Se debe implementar un motor de evaluación que pruebe las reglas sobre la estructura real del grafo antes de promoverlas, además de edición y parametrización avanzada de reglas dentro del sandbox antes de publicarlas a producción.

Origen: `notas.md` → [ISSUE-05] Motor de Reglas para Policy Sandbox (→ #521).

## Status: DONE (2026-09-28)

## Priority: MEDIUM

## Component
Frontend / Governance / Sandbox / Rules

## Type
feat / governance

## Implementation
1. **Motor de reglas:** `utils/ruleEngine.ts` que evalúa reglas expresadas como DSL JSON (scope, profundidad, restricciones de tecnología, naming, severidad) sobre datos reales del grafo (API `/graph/dependencies`, `componentsApi`, `analysisApi`; fallback a los datos sembrados del store cuando no hay backend); límites de profundidad, nodos visitados y timeouts para reglas expansivas.
2. **Evaluación pre-promoción:** botón "Simulate against real graph" que devuelve nodos que hacen match, violaciones detectadas y blast radius; el informe de impacto actual pasa a alimentarse de este resultado en lugar de fixtures predefinidas.
3. **Editor avanzado de reglas:** `RuleEditorModal` con parametrización completa (tipo de regla, parámetros, severidad, alcance por tecnología/proyecto), preview de la evaluación y borrador persistido en `sandboxStore`; el botón "Promote to production" envía la regla vía `policiesStore.createPolicy` → `POST /api/v1/policies` real (fallback mock).
4. i18n + build + smoke con backend.

## Acceptance Criteria
- [x] Rule engine evaluates rules against the real graph structure (not predefined fixtures)
- [x] Advanced in-sandbox rule editing: parameters, scope, severity, draft persistence
- [x] Impact report shows matching nodes, violations and blast radius before promotion
- [x] Promote sends the rule to the real policies API (mock fallback preserved)
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Verification (2026-09-28)

- Frontend: `npm run lint` 0 errors (2 pre-existing warnings), `npm test` 113/113 (new `utils/ruleEngine.spec.ts` 22 tests), `npm run build` green (vue-tsc + vite); backend untouched (gates sin cambios).
- Docker (:19001): `tasker-board` rebuilt from the fresh `dist/`, 4 containers healthy; smoke → page 200, served bundle contains the `PolicySandboxView` chunk + new i18n keys, `GET /api/v1/graph/dependencies` → real Neo4j nodes/edges, `POST /api/v1/policies` with the mapped body → 201 (`target_scope: PROJECT`, `severity: BLOCKER`, `logic_definition` stored, policy `c48bfc24…`).

## Files to Create
- `frontend/src/utils/ruleEngine.ts` (o `frontend/src/api/sandboxApi.ts`)
- `frontend/src/components/sandbox/RuleEditorModal.vue`

## Files to Modify
- `frontend/src/stores/sandboxStore.ts` — evaluación real, borradores
- `frontend/src/views/PolicySandboxView.vue` — simulación real + editor
- `frontend/src/api/policiesApi.ts` — promoción real de reglas
- `frontend/src/locales/en.json` / `es.json` — rule editor / simulate
- `features.md` — cuando esté done

## Related Issues
- #84 (Graph Policy Engine), #82 (Active Policy Enforcement), #85 (Pre-Execution Validation), #490 (Policy Sandbox), #501 (Governance Validation Modal), #511 (Graph Exploration & Inspector)
