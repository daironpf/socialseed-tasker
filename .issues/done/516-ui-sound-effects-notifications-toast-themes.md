# Issue #516: UI Sound Effects, Notifications Center & Toast Theme System

## Description

Aumentar la calidad del producto (*delight factors*) con un centro de notificaciones robusto, respuestas hápicas/auditivas opcionales para eventos críticos (Kill Switch, fallos de ejecución, éxitos de auto-healing) y un sistema de avisos pulido.

Origen: `notas.md` → Issue #508 (renumerada a #516; #508 ya está en done como Mobile Responsive).

## Status: DONE

## Resolution
- **NotificationCenter agrupado:** panel evolucionado con grupos de criticidad Emergency (constraint_violation, agent_failure, sla) / Warning (hitl) / Info (mention) con headers sticky, chips de filtro por canal (All/HITL/Governance/Agent/SLA/Mentions), bulk "Mark read" por grupo y "Clear all"; nuevos `markManyRead`/`dismissMany` en `notificationsStore`.
- **Sonido configurable:** `composables/useSoundEffects.ts` con Web Audio API (osciladores, sin assets): `playAlert` (Kill Switch/fallos/SLA), `playSuccess` (auto-healing), `playPing` (HITL/mentions); on/off + volumen 0-100 persistidos en localStorage; sin autoplay hasta la primera interaccion (`gestured` en pointerdown/keydown).
- **Preferencias por canal:** `notificationsStore.preferences` (`socialseed-alert-prefs`): sonido on/off por categoria (mention off por defecto); `addNotification` dispara `playForCategory` segun preferencias; seed/HITL directos no suenan.
- **Nueva categoria `sla`:** `NotificationCategory` + `CATEGORY_CONFIG` + `SEVERITY_GROUPS` (emergency/warning/info); `AnalyticsDashboardView` notifica ahora con categoria `sla`.
- **Toast theme system:** `uiStore.toastTheme` (minimal/rich/enterprise) persistido en `toast-theme`; `ToastItem` con variantes visuales (minimal = bordes grises planos, rich = actual, enterprise = barra superior de color + label mono + border-left); `ToastThemeSettings` con 3 previews mini.
- **UserMenu:** seccion Alerts con toggle de sonido, slider volumen, boton de test (`playPing`) y selector de tema de toasts.
- **Hooks de evento:** `IssueCard.killAgent` -> `playAlert`; `autoHealingStore.simulateCompletion` (run running -> completed + log + `playSuccess`) con boton "Simulate pipeline success" en `AutoHealingMonitorView`.
- i18n: secciones nuevas `soundEffects` + `toastTheme` + `notifPanel` y `autoHealing.simulateSuccess` (EN/ES, 73 secciones totales). `npm run build` pasa (42.70s).


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
- [x] Floating NotificationCenter panel groups history by criticality (Info, Warning, Emergency)
- [x] Subtle, configurable sound effects for high-severity alerts and successful auto-healing
- [x] Mark notifications read, filter by channel, customize user alert preferences
- [x] Sound on/off + volume persist; no sound before user gesture
- [x] Toast theme system with selectable styles persisted
- [x] Integrates with existing notifications from #507 HITL and future SLA alerts
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

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
