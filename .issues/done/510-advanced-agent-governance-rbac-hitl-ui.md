# Issue #510: Advanced Agent Governance, RBAC & Granular Human-in-the-Loop Approval UI

## Description

Las empresas requieren control estricto sobre lo que un agente IA puede ejecutar automáticamente vs. lo que requiere aprobación humana previa (Human-in-the-Loop). La UI debe reflejar una matriz detallada de permisos y flujos de aprobación paso a paso con interacciones simuladas completas, sobre la capa mock actual.

Origen: `notas.md` → Issue #502 (renumerada a #510; #502 ya está en done).

## Status: DONE

### Resolution (2026-09-24)

Implementado completo en frontend (mock, sin backend nuevo):

- **Tipos**: `frontend/src/types/governance.ts` — `GovernanceAgentType` (CODING/DEPLOY/DATA/OPS), `GovernanceRiskLevel` (LOW/MEDIUM/HIGH/CRITICAL), `GovernanceActionId` (write_code, push_pr, modify_db, delete_resource, deploy, config_change, external_api), `PermissionState` (auto/approval/blocked), `PermissionMatrix`, `RestrictedActionAlert` + arrays de constantes.
- **Store**: `frontend/src/stores/governanceStore.ts` — matriz con seeds por defecto (p.ej. push_pr requiere aprobación, delete_resource a HIGH/CRITICAL bloqueado), carga/persistencia en `localStorage` (`governance-matrix-v1`), `toggleCell` cicla estados, `resetMatrix`, `simulateRestrictedAction` (pausa el issue vía `issuesStore.updateIssue({ agent_working:false })` cuando el estado es `approval`) y `resolveAlert` (aprobar → reanuda `agent_working:true`).
- **Vista**: `frontend/src/views/GovernanceMatrixView.vue` en `/governance-matrix` — tabs de nivel de riesgo, tabla acciones × tipo de agente con celdas editables (clic cicla Auto→Aprobación→Bloqueado), leyenda, reset a defaults, simulador de acción restringida (agente/riesgo/acción/issue) que crea alertas en vivo con botones "Aprobar y reanudar" / "Rechazar y mantener detenido", toast + notificación `requiresAction:true` (categoría hitl) por `notificationsStore`.
- **Cola de aprobaciones**: `frontend/src/components/governance/PendingApprovalsQueue.vue` — lista de `hitlStore.pendingRequests`, detalle con metadatos de agente, 3 tiles de impacto (totalAffected/directDeps/riskLevel), `DiffViewer` inline por fichero, acciones Approve / Request Changes / Reject con feedback obligatorio; resolución vía `hitlStore.resolveAction` + `issuesStore.updateIssue` (approve/modify → IN_PROGRESS, reject → OPEN — consistente con #507/HITLQuickActionModal) + toast + notificación `requiresAction:false`.
- **Integración**: ruta `GovernanceMatrix` en router, entradas Sidebar + MobileDrawer (Management), título de header, sección i18n `governanceMatrix.*` + `nav.governanceMatrix` + `header.governanceMatrix` EN/ES.
- **Build**: `npm run build` (vue-tsc + vite) pasa sin errores.

Acceptance Criteria todos cumplidos. `ApprovalDiffPanel` no fue necesario: se reutiliza `DiffViewer` inline (opción permitida por la issue). Endpoints mock nuevos no requeridos (matriz persistida en localStorage, HITL ya usa mock del store).

## Priority: HIGH

## Component
Frontend / Governance / RBAC / HITL

## Type
feat / governance

## Implementation
1. **Vista `GovernanceMatrixView`:**
   - Nueva vista + ruta `/governance-matrix`
   - Matriz de permisos por tipo de agente × nivel de riesgo
   - Acciones configurables: Write Code, Push to PR, Modify DB, Delete Resource, Deploy, etc.
   - Estados por celda: Auto-allowed / Requires approval / Blocked
   - Edición simulada persistida (store + localStorage o mock API)

2. **Cola de Aprobaciones Pendientes (Pending Approvals Queue):**
   - Panel (en GovernanceMatrix o HITLCommandCenter) con cola de solicitudes
   - Por cada solicitud: Diff Viewer (`DiffViewer.vue`), análisis de impacto previo mock, metadatos de agente
   - Acciones: Aprobar / Rechazar / Solicitar Cambios (con comentario)
   - Integrar con `hitlStore.resolveAction` y estados de issue (`WAITING_HUMAN_APPROVAL`)

3. **Alertas en vivo de acción restringida:**
   - Simular cuando un agente intenta una acción restringida: banner/modal tipo HITL
   - Pausar la "ejecución" mock del agente (flag en issue / `agent_working`)
   - Reanudar solo tras decisión del usuario; toast + notificación `requiresAction`

4. **Extender `policiesStore` / governance mock:**
   - Reglas de riesgo por acción y rol de agente
   - Wire con `GovernanceValidationModal` existente sin romper cierre de issues

## Acceptance Criteria
- [ ] `GovernanceMatrixView` configures permission rules per agent type and risk level (Write Code, Push to PR, Modify DB, Delete Resource)
- [ ] Pending Approvals Queue with Diff Viewer, pre-impact analysis, and Approve / Reject / Request Changes
- [ ] Live alerts when an agent attempts a restricted action; simulated execution pauses until user action
- [ ] Resolutions update HITL requests and related issue status consistently with #507
- [ ] Matrix state persists in mock mode across reloads
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/views/GovernanceMatrixView.vue`
- `frontend/src/components/governance/PendingApprovalsQueue.vue`
- `frontend/src/components/governance/ApprovalDiffPanel.vue` (or reuse DiffViewer inline)
- `frontend/src/stores/governanceStore.ts` (or extend `policiesStore` + `hitlStore`)
- `frontend/src/types/governance.ts`

## Files to Modify
- `frontend/src/router/index.ts` — add `/governance-matrix`
- `frontend/src/components/layout/Sidebar.vue` / `MobileDrawer.vue` — nav entry
- `frontend/src/stores/hitlStore.ts` — queue integration, request-changes flow
- `frontend/src/stores/issuesStore.ts` — pause/resume agent on restricted action
- `frontend/src/components/ui/HITLQuickActionModal.vue` — optional deeper actions
- `mock-api/server.py` — governance matrix + approvals endpoints (optional)
- `frontend/src/locales/en.json` / `es.json` — governanceMatrix, approvalsQueue sections
- `features.md` — when done

## Related Issues
- #501 (Governance Validation Modal), #507 (HITL Quick Actions), #489 (HITL Command Center), #471 (HITL Approval Gateways), #82 (Active Policy Enforcement), #509 (Multi-Tenancy — roles feed RBAC)
