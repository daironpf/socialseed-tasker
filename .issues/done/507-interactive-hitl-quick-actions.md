# Issue #507: Interactive HITL Control Center with Quick Actions

## Description

El `HITLCommandCenter` muestra solicitudes que requieren aprobación humana. Debemos conectar estas solicitudes con notificaciones flotantes (Toast/Banner) para tomar decisiones instantáneas desde cualquier parte de la aplicación, sin tener que navegar manualmente a la vista HITLCommandCenter.

## Status: DONE

## Priority: HIGH

## Component
Frontend / HITL / Global Actions

## Implementation
1. **Banner Global de HITL Pendiente:**
   - Si en `hitlStore` existe alguna solicitud en estado `PENDING` con severidad `CRITICAL` o `HIGH`, desplegar una barra de notificación persistente en `AppHeader`
   - Banner con contador de solicitudes pendientes
   - Click en banner -> navega a HITLCommandCenter

2. **Modal de Acción Rápida HITL:**
   - Crear `HITLQuickActionModal.vue`
   - Al hacer clic en "Review" desde el banner o notificación, abrir modal rápido
   - Modal muestra: request title, severity, description, agent info
   - Acciones: Approve, Reject, Modify (con textarea para comentarios)
   - Botón "View Full Context" -> navega a HITLCommandCenter

3. **Actualización del Estado en Mock:**
   - Al resolver solicitud HITL, cambiar dinámicamente el estado del issue asociado de `WAITING_HUMAN_APPROVAL` a `IN_PROGRESS` o `OPEN`
   - Actualizar `hitlStore` con el nuevo estado
   - Emitir toast de confirmación

4. **Integración con Notificaciones:**
   - Crear notificación automática cuando llega solicitud HITL PENDING
   - Marcar como "requires action"
   - Click-through abre modal de acción rápida

## Acceptance Criteria
- [x] Global HITL banner shows in AppHeader when critical/high requests pending
- [x] Banner shows count of pending requests
- [x] Click banner navigates to HITLCommandCenter
- [x] Quick action modal opens with approve/reject/modify
- [x] Modify action allows text input
- [x] Approve/Reject updates issue status dynamically
- [x] Toast notification confirms action
- [x] Notification created automatically for new HITL requests
- [x] i18n support (EN + ES)

## Files to Create
- `frontend/src/components/ui/HITLQuickActionModal.vue`

## Files to Modify
- `frontend/src/components/layout/AppHeader.vue` — add global HITL banner
- `frontend/src/stores/hitlStore.ts` — add resolveAction method
- `frontend/src/stores/issuesStore.ts` — update issue status on HITL resolution
- `frontend/src/stores/notificationsStore.ts` — auto-create HITL notifications
- `frontend/src/locales/en.json` — add hitlQuickAction section
- `frontend/src/locales/es.json` — add hitlQuickAction section

## Related Issues
- #489 (HITL Command Center), #475 (Notification Center), #501 (Governance Validation)
