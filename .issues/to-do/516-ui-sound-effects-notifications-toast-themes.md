# Issue #516: UI Sound Effects, Notifications Center & Toast Theme System

## Description

Aumentar la calidad del producto (*delight factors*) con un centro de notificaciones robusto, respuestas hápicas/auditivas opcionales para eventos críticos (Kill Switch, fallos de ejecución, éxitos de auto-healing) y un sistema de avisos pulido.

Origen: `notas.md` → Issue #508 (renumerada a #516; #508 ya está en done como Mobile Responsive).

## Status: TODO

## Priority: LOW

## Component
Frontend / Notifications / Sound / Polish

## Type
feat / polish

## Implementation
1. **Panel flotante de NotificationCenter mejorado:**
   - Evolucionar `NotificationCenter.vue`: historial agrupado por criticidad (Info, Warning, Emergency)
   - Agrupación por canal/fuente (HITL, Governance, Agent, Sync, SLA)
   - Estilo flotante coherente con mobile (#508); acciones bulk (mark group read, clear)

2. **Efectos de sonido configurables (`SoundEffects`):**
   - Composable `useSoundEffects.ts` con clips Web Audio API (osciladores/beeps sin assets binarios obligatorios) o archivos `public/sounds/` opcionales
   - Eventos: alerta alta severidad (Kill Switch, fallo agente), resolución exitosa de auto-healing, notificación Emergency
   - Preferencia on/off + volumen en UserMenu o Profile (persistencia localStorage)
   - Nunca autoplay agresivo: respetar primera interacción del usuario

3. **Preferencias y filtrado de alertas:**
   - Marcar notificaciones como leídas (ya existe) + marcar grupo
   - Filtrar por canal en el panel
   - Personalizar preferencias: qué canales suenan / push visual / solo toast
   - Extender `notificationsStore` con `preferences`

4. **Toast theme system:**
   - Temas visuales para `ToastContainer`/`ToastItem` (minimal / rich / enterprise)
   - Opción de iconos más expresivos y progress bar (parcial en ToastItem ya)
   - Persistencia de tema en localStorage

## Acceptance Criteria
- [ ] Floating NotificationCenter panel groups history by criticality (Info, Warning, Emergency)
- [ ] Subtle, configurable sound effects for high-severity alerts and successful auto-healing
- [ ] Mark notifications read, filter by channel, customize user alert preferences
- [ ] Sound on/off + volume persist; no sound before user gesture
- [ ] Toast theme system with selectable styles persisted
- [ ] Integrates with existing notifications from #507 HITL and future SLA alerts
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/composables/useSoundEffects.ts`
- `frontend/src/components/notifications/NotificationCenterPanel.vue` (or evolve existing)
- `frontend/src/components/ui/ToastThemeSettings.vue`

## Files to Modify
- `frontend/src/components/ui/NotificationCenter.vue` — grouping by criticality/channel
- `frontend/src/components/ui/NotificationItem.vue` — group actions if needed
- `frontend/src/stores/notificationsStore.ts` — preferences, channel filter, groups
- `frontend/src/components/ui/ToastContainer.vue` / `ToastItem.vue` — theme system
- `frontend/src/components/layout/UserMenu.vue` — sound + toast theme toggles
- `frontend/src/views/ProfileView.vue` — alert preference section (optional)
- `frontend/src/stores/autoHealingStore.ts` — trigger success sound (or in view)
- `frontend/src/locales/en.json` / `es.json` — soundEffects, toastTheme, notificationChannels
- `features.md` — when done

## Related Issues
- #475 (Notification Center Inbox), #476 (Toast Notification System), #507 (HITL Quick Actions notifications), #508 (Mobile Responsive), #494 (Auto-Healing), #503 (Agent Kill Switch)
