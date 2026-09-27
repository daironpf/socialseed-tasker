# Issue #523: Keyboard Navigation & Accessibility (WCAG 2.1)

## Description

Las teclas de navegación en listas (`J`/`K`/`Enter`) figuran en el modal de ayuda (`KeyboardShortcutsHelp`) pero no están suscritas en el composable `useKeyboardShortcuts`. Además se requiere una auditoría de accesibilidad: contraste de colores, compatibilidad con lectores de pantalla y foco de teclado en modales y paneles laterales (WCAG 2.1).

Origen: `notas.md` → [ISSUE-07] Navegación por Teclado e Accesibilidad (WCAG 2.1) (→ #523).

## Status: TODO

## Priority: LOW

## Component
Frontend / UX / Accessibility

## Type
accessibility / ux

## Implementation
1. **Atajos `J`/`K`/`Enter`:** registrarlos con scope `local` en `ListView` y `KanbanView`: navegación por filas/tarjetas con elemento resaltado (`aria-activedescendant`), `Enter` abre el detalle de la issue seleccionada (router push); actualizar `KeyboardShortcutsHelp` para reflejar el comportamiento real (hoy documenta atajos no suscritos) y la §20 de `features.md`.
2. **Foco en overlays:** composable `useFocusTrap.ts` (Tab cicla, ESC cierra, devuelve foco al disparador) aplicado a `CreateIssueModal`, `GovernanceValidationModal`, `CommandPalette` y `SyncQueueDrawer`; `aria-label`/`role`/`aria-modal` en modales y paneles; skip-to-content link en el shell.
3. **Auditoría visual:** contraste WCAG AA de pares de color en modo oscuro (texto secundario, chips, bordes), foco visible (`:focus-visible`) en todos los controles interactivos, navegación por tab del tablero Kanban.
4. **Verificación:** recorrido solo con teclado de los flujos principales + comprobación de contraste + `npm run build`.

## Acceptance Criteria
- [ ] `J` (next) / `K` (previous) / `Enter` (open) subscribed for lists and boards with visible focus
- [ ] Help modal documents only shortcuts that are actually registered
- [ ] Modals and side panels: focus trap, ESC close, focus restore, aria labels
- [ ] Color contrast meets WCAG 2.1 AA; keyboard-only navigation of main flows works
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/composables/useFocusTrap.ts`

## Files to Modify
- `frontend/src/composables/useKeyboardShortcuts.ts` — registrar J/K/Enter locales
- `frontend/src/views/ListView.vue` — navegación y apertura con teclado
- `frontend/src/views/KanbanView.vue` — navegación y apertura con teclado
- `frontend/src/components/ui/KeyboardShortcutsHelp.vue` — documentación real
- `frontend/src/components/issue/CreateIssueModal.vue` / `GovernanceValidationModal.vue` / `sync/SyncQueueDrawer.vue` — focus trap + aria
- `frontend/src/locales/en.json` / `es.json` — textos de ayuda
- `features.md` — §20/§50 cuando esté done

## Related Issues
- #467 (Command Palette Cmd+K), #468 (Keyboard Shortcuts Composable), #508 (Mobile Responsive), #516 (Help/notification polish)
