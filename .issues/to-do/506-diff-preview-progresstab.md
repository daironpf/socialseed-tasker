# Issue #506: Diff Preview in ProgressTab

## Description

Actualmente, la pestaña ProgressTab en `IssueDetailView.vue` enumera los archivos afectados (`affected_files`). Sin embargo, la UI no permite previsualizar el código modificado o la propuesta de cambio del agente. Se debe integrar el componente `DiffViewer` existente para mostrar diffs de código mock.

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Issue Detail / ProgressTab

## Implementation
1. **Mock de Diff de Código en `issues.json`:**
   - Extender `affected_files` para incluir `diff_hunk?: string` (formato estándar de Git diff)
   - Generar diffs realistas para archivos EDITED (mostrar líneas agregadas/eliminadas)
   - CREATED files: diff completo del archivo
   - DELETED files: diff con eliminaciones

2. **Integrar `DiffViewer.vue` en ProgressTab:**
   - Añadir botón "View Changes" junto a cada archivo modificado en `IssueDetailView.vue`
   - Al hacer clic, desplegar un accordion o inline expand con `DiffViewer.vue`
   - Soportar vista Unificada y Lado a Lado

3. **Tipos Extendidos:**
   - Agregar `diff_hunk` opcional a `AffectedFile` interface
   - Agregar `language?: string` para syntax highlighting

4. **Estilo:**
   - Colapsar diffs por defecto (mostrar solo nombre del archivo + badge)
   - Expandir con animación suave
   - Botón "Copy" para copiar el diff

## Acceptance Criteria
- [ ] `affected_files` includes `diff_hunk` in mock data
- [ ] "View Changes" button visible for EDITED/CREATED files
- [ ] DiffViewer expands inline showing unified/split view
- [ ] Language detection for syntax highlighting
- [ ] Copy diff button works
- [ ] Collapsed by default, expands with animation
- [ ] i18n support (EN + ES)

## Files to Modify
- `frontend/src/types/index.ts` — add diff_hunk and language to AffectedFile
- `frontend/src/views/IssueDetailView.vue` — add "View Changes" button and DiffViewer integration
- `frontend/src/dataset-de-pruebas/issues.json` — add diff_hunk data to affected_files
- `frontend/src/locales/en.json` — add diff preview keys
- `frontend/src/locales/es.json` — add diff preview keys

## Related Issues
- #502 (Tech Debt & Affected Files), #47 (Issue Detail Panel)
