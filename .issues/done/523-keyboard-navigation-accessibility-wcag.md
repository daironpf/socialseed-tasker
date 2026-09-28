# Issue #523: Keyboard Navigation & Accessibility (WCAG 2.1)

## Description

Las teclas de navegación en listas (`J`/`K`/`Enter`) figuran en el modal de ayuda (`KeyboardShortcutsHelp`) pero no están suscritas en el composable `useKeyboardShortcuts`. Además se requiere una auditoría de accesibilidad: contraste de colores, compatibilidad con lectores de pantalla y foco de teclado en modales y paneles laterales (WCAG 2.1).

Origen: `notas.md` → [ISSUE-07] Navegación por Teclado e Accesibilidad (WCAG 2.1) (→ #523).

## Status: DONE (2026-09-28)

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
- [x] `J` (next) / `K` (previous) / `Enter` (open) subscribed for lists and boards with visible focus
- [x] Help modal documents only shortcuts that are actually registered
- [x] Modals and side panels: focus trap, ESC close, focus restore, aria labels
- [x] Color contrast meets WCAG 2.1 AA; keyboard-only navigation of main flows works
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

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

## Verification (2026-09-28)
- `npm run lint`: 0 errores (2 warnings preexistentes `vue/no-mutating-props` en IssueDetailView)
- `npm test`: 140/140 (17 ficheros; 16 tests nuevos: useFocusTrap 5, useKeyboardShortcuts +5, KeyboardShortcutsHelp 3, CreateIssueModal 3, ListView 3, KanbanView 2)
- `npm run build`: verde (vue-tsc + vite)
- Smoke HTTP en :19001 tras `docker compose build tasker-board && docker compose up -d`: contenedores healthy; bundle principal sirve skip link + claves `a11y`/`palette` (ES), chunks `ListView`/`KanbanView` contienen `aria-activedescendant`/`listbox`/`issue-card-`, CSS sirve `:focus-visible`
- features.md §20 actualizada (tabla local shortcuts + subsección "Accessibility - WCAG 2.1"; eliminada la nota de atajos no suscritos)
