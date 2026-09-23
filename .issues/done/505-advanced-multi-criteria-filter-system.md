# Issue #505: Advanced Multi-Criteria Filter System

## Description

Aunque existen filtros individuales por estado, prioridad y proyecto, la UI carece de una barra de filtros combinados (multi-tag) que permita guardar búsquedas frecuentes o filtrar por rango de fechas, tags y asignados. Se requiere un componente `FilterBuilder` visual reutilizable.

## Status: DONE

## Priority: HIGH

## Component
Frontend / Issues / Filter System

## Implementation
1. **Componente `FilterBuilder.vue`:**
   - Chips de filtros activos (ej: `Priority: HIGH` × `Assignee: Agent-01` × `Has Tech Debt: true`)
   - Opción para limpiar todos los filtros de un clic (`Clear All`)
   - Soporte para operadores AND/OR
   - Filtros disponibles: status, priority, assignee, component, labels, hasTechDebt, hasAffectedFiles, dateRange

2. **Actualizar `issuesStore.ts`:**
   - Ampliar `filteredIssues` para evaluar condiciones compuestas
   - Soportar filtrado por existencia de deuda técnica (`technical_debt_notes`)
   - Soportar filtrado por presencia de archivos afectados (`affected_files.length > 0`)
   - Soportar filtrado por rango de fechas (`created_at`)

3. **Persistencia Mock:**
   - Guardar combinaciones de filtros en `localStorage` bajo "Saved Searches"
   - Cargar búsquedas guardadas al inicio
   - Máximo 10 búsquedas guardadas

4. **Integración en Vistas:**
   - `ListView.vue`: FilterBuilder en la barra de herramientas
   - `KanbanView.vue`: FilterBuilder en el header
   - `GraphView.vue`: FilterBuilder existente mejorado

## Acceptance Criteria
- [ ] `FilterBuilder.vue` component created with chip-based UI
- [ ] Multi-criteria filtering works (AND/OR operators)
- [ ] Filter by tech debt existence works
- [ ] Filter by affected files works
- [ ] Filter by date range works
- [ ] Saved searches persist in localStorage
- [ ] Clear All button resets all filters
- [ ] Filter chips are removable individually
- [ ] ListView, KanbanView, GraphView all use FilterBuilder
- [ ] i18n support (EN + ES)

## Files to Create
- `frontend/src/components/ui/FilterBuilder.vue`

## Files to Modify
- `frontend/src/stores/issuesStore.ts` — extended filteredIssues with composite conditions
- `frontend/src/views/ListView.vue` — integrate FilterBuilder
- `frontend/src/views/KanbanView.vue` — integrate FilterBuilder
- `frontend/src/locales/en.json` — add filterBuilder section
- `frontend/src/locales/es.json` — add filterBuilder section

## Related Issues
- #498 (Project Selector), #502 (Tech Debt & Affected Files)
