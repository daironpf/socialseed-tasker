# Issue #529: Análisis de impacto y causa raíz en modo real

## Description

`AnalysisView` funciona contra el mock: `frontend/src/api/analysisApi.ts` llama a `/analysis/impact/{id}`, `/analysis/root-cause` y `/test-failures`, pero el backend real expone `/api/v1/analyze/impact/{issue_id}` y `/api/v1/analyze/root-cause`, y **no existe** ningún endpoint `/test-failures` en el backend. En modo real el panel de impacto/causa raíz recibe 404 y el formulario de fallos de test no carga.

Origen: `notas.md` → ÉPICA 2 · Issue #6 (→ #529). Las insignias de riesgo (`LOW/MEDIUM/HIGH/CRITICAL`), la cascada de bloqueados y los paneles ya existen (#68, #74, #216): esta issue cubre el desajuste de contrato backend↔frontend.

## Status: DONE (2026-09-30)

## Priority: HIGH

## Component
Frontend + Backend / Analysis / Integration

## Type
bug / integration

## Implementation
1. **Alinear rutas del frontend:** `analysisApi.ts` → `GET /analyze/impact/{id}` y `POST /analyze/root-cause` en modo real; actualizar el dispatch mock de `client.ts`/`mockApi.ts` (o añadir aliases `/analysis/*` en backend para compatibilidad).
2. **`GET /api/v1/test-failures`:** endpoint real con envelope `APIResponse` (fuente: fallos registrados/dataset); sin datos responde lista vacía para que "Load Sample" degrade sin error.
3. **Contrato de respuesta:** verificar que `ImpactAnalysisResponse` (incluye `risk_level`, `blocked_issues`, `directly/transitively_affected`) mapea al tipo `ImpactAnalysis` del frontend; documentar el body esperado por `/analyze/root-cause` frente a los parámetros del formulario (test name, component, error message, labels).
4. **Verificación en modo real:** smoke con API real (Docker): impacto con risk badge, bloqueados en cascada y resultados de causa raíz.

## Acceptance Criteria
- [x] Impacto y causa raíz consumen `GET /analyze/impact/{id}` y `POST /analyze/root-cause` en modo real (sin 404)
- [x] `GET /test-failures` responde en el backend real (lista vacía = caso válido documentado)
- [x] Insignias de riesgo (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`) y lista de tareas bloqueadas en cascada desde la respuesta real
- [x] Modo mock intacto; i18n (EN + ES); `npm run build` passes
- [x] Gates backend sin regresiones

## Files to Create
- `frontend/src/api/analysisApi.spec.ts` — rutas `/analyze/*` + `test_id` generado
- Tests backend en `tests/unit/test_api.py::TestAnalysis` (fixture `client` existente): contrato de impacto, confianza porcentaje, `/test-failures` (vacío y derivado), subgraph

## Files to Modify
- `frontend/src/api/analysisApi.ts` — rutas `/analyze/*` + `test_id: manual-<ts>` en el body
- `frontend/src/api/client.ts` — dispatch mock a `/analyze/impact/*` y `/analyze/root-cause`
- `src/socialseed_tasker/infrastructure/web_api/routers/analysis.py` — `GET /test-failures`; `issue_status`/`confidence%` en causa raíz; campos extra de impacto; fix `queue.poplept()`→`popleft()` y `nodes` dict→list en `/graph/{id}/subgraph`
- `src/socialseed_tasker/infrastructure/web_api/schemas.py` — `TestFailureResponse` nuevo; `ImpactAnalysisResponse` (+`issue_title`, `issue_status`, `graph_depth`, `total_affected`); `CausalLinkResponse` (+`issue_status`)
- `src/socialseed_tasker/application/analyzer.py` — `ImpactAnalysis.graph_depth` calculado en el BFS
- `features.md` — §13 (tabla "Real API contract (#529)")

## Verification
**Contrato (documentado en `features.md` §13):**
- `GET /analyze/impact/{id}` → `ImpactAnalysisResponse` mapea 1:1 al tipo `ImpactAnalysis` del frontend (`issue_title`, `issue_status`, `risk_level`, `graph_depth`, `total_affected`, `directly/transitively_affected`, `blocked_issues`, `affected_components`).
- `POST /analyze/root-cause` body: `{test_id, test_name, error_message, component?, labels[]}` — el frontend genera `test_id` (`manual-<timestamp>`); `confidence` ahora se devuelve en **porcentaje 0–100** (antes 0–1 la UI mostraba "1%") y se añade `issue_status`.
- `GET /test-failures` deriva los fallos de los issues con label `test-failure` (creados por `POST /webhooks/test-failure`, parseando `**Error Message:**` de la descripción); sin datos → `data: []`.

**Gates (2026-09-30):** ruff `src/` = **1011** (= baseline), mypy = **1154/133** (≤ baseline 1155/133), pytest = **1146 passed / 27 skipped / 3 failed** (mismos 3 fallos preexistentes), eslint 0 errores (2 warnings preexistentes), vitest **183/183** (178 + 5 nuevos), `npm run build` verde.

**Smoke real (Docker `tasker-api` + `tasker-board` reconstruidos, `X-API-Key: test-token`):**
- `GET /api/v1/test-failures` → 200 `data: []`; tras `POST /webhooks/test-failure` → 200 con el registro derivado (`test_name` sin prefijo, `error_message` parseado, `component`, `failed_at`, `labels`).
- `GET /api/v1/analyze/impact/{id}` → 200 con `issue_title`, `issue_status`, `graph_depth: 1`, `total_affected: 1`, `risk_level: MEDIUM`, `blocked_issues` con la cascada.
- `POST /api/v1/analyze/root-cause` → 200 con `confidence: 100.0` (%), `issue_status: CLOSED`, `reasons`.
- `GET /api/v1/graph/{id}/subgraph` → 200 (regresión de los fixes `poplept`→`popleft` y `nodes` dict→list).

**Smoke mock (Playwright temporal, `tasker-board:19001`, borrado):** selector de impacto → `ISS-001 — Fix login validation...` + risk badge; causa raíz → 10 candidatos, top `40%`; **0 pageerrors**; único HTTP ≥400 el 404 preexistente `/mock-api/mock/organizations` (verificado igual antes del cambio).

## Related Issues
- #68 (Component impact analysis), #74 (Root-cause clarity), #100 (Fix analysis endpoints), #114 (Analysis 404), #216 (Enhanced impact analysis), #517 (real mode), #519 (gates de roles)
