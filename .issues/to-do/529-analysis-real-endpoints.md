# Issue #529: Análisis de impacto y causa raíz en modo real

## Description

`AnalysisView` funciona contra el mock: `frontend/src/api/analysisApi.ts` llama a `/analysis/impact/{id}`, `/analysis/root-cause` y `/test-failures`, pero el backend real expone `/api/v1/analyze/impact/{issue_id}` y `/api/v1/analyze/root-cause`, y **no existe** ningún endpoint `/test-failures` en el backend. En modo real el panel de impacto/causa raíz recibe 404 y el formulario de fallos de test no carga.

Origen: `notas.md` → ÉPICA 2 · Issue #6 (→ #529). Las insignias de riesgo (`LOW/MEDIUM/HIGH/CRITICAL`), la cascada de bloqueados y los paneles ya existen (#68, #74, #216): esta issue cubre el desajuste de contrato backend↔frontend.

## Status: TODO

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
- [ ] Impacto y causa raíz consumen `GET /analyze/impact/{id}` y `POST /analyze/root-cause` en modo real (sin 404)
- [ ] `GET /test-failures` responde en el backend real (lista vacía = caso válido documentado)
- [ ] Insignias de riesgo (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`) y lista de tareas bloqueadas en cascada desde la respuesta real
- [ ] Modo mock intacto; i18n (EN + ES); `npm run build` passes
- [ ] Gates backend sin regresiones

## Files to Create
- `tests/api/test_analysis_endpoints_unit.py` — cobertura de `/analyze/*` + nuevo `/test-failures`
- `frontend/src/api/analysisApi.spec.ts`

## Files to Modify
- `frontend/src/api/analysisApi.ts` — rutas `/analyze/*`
- `frontend/src/api/client.ts` / `frontend/src/api/mockApi.ts` — dispatch y paths mock
- `src/socialseed_tasker/infrastructure/web_api/routers/analysis.py` — `GET /test-failures` (o alias)
- `features.md` — §13

## Related Issues
- #68 (Component impact analysis), #74 (Root-cause clarity), #100 (Fix analysis endpoints), #114 (Analysis 404), #216 (Enhanced impact analysis), #517 (real mode), #519 (gates de roles)
