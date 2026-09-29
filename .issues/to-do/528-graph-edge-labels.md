# Issue #528: Graph View — etiquetas explícitas de aristas

## Description

`GraphView` dibuja las relaciones como flechas sin etiqueta: los tipos (`relation: 'dependency' | 'component' | 'agent' | ...`) solo se muestran al inspeccionar la arista en el `Edge inspector`. La ÉPICA 2 de `notas.md` exige "dibujar bordes con etiquetas explícitas: `DEPENDS_ON`, `BLOCKS`, `AFFECTS` y `BELONGS_TO`". El resto del visualizador (nodos Issue/Component, filtros por estado y componente, zoom/pan/drag, panel lateral al clicar) ya está implementado (#53, #80, #511): esta issue cubre solo el gap de etiquetas.

Origen: `notas.md` → ÉPICA 2 · Issue #5 (→ #528).

## Status: TODO

## Priority: LOW

## Component
Frontend / Graph / Visualization

## Type
feat / visualization

## Implementation
1. **Etiquetas en aristas:** configurar el `label` de vis-network por relación real: `DEPENDS_ON` (issue → dependencia), `BELONGS_TO` (issue → componente), `AFFECTS` (aristas de impacto/código del overlay) y `BLOCKS` para la dirección bloqueante → bloqueado derivada de las cadenas de dependencia (los grafos actuales no tienen relación `:BLOCKS` propia; se etiqueta la arista inversa de la dependencia que causa el bloqueo).
2. **Toggle de etiquetas:** control en `GraphFilters`/`GraphToolbar` para mostrar/ocultar etiquetas (visibles por defecto, ocultables para grafos densos).
3. **Leyenda e inspector:** la leyenda y el `Edge inspector` existentes pasan a usar los mismos nombres de relación (i18n `graphExplorer.relations.*`).
4. **Rendimiento:** fuente compacta coloreada por tipo; verificar con 100 issues + componentes que el grafo no se degrade.

## Acceptance Criteria
- [ ] Cada arista muestra su tipo como etiqueta visible (`DEPENDS_ON`, `BLOCKS`, `AFFECTS`, `BELONGS_TO`)
- [ ] Toggle para mostrar/ocultar etiquetas sin recargar el grafo
- [ ] Leyenda e inspector de aristas consistentes con las etiquetas mostradas
- [ ] i18n support (EN + ES)
- [ ] `npm run build` passes

## Files to Create
- `frontend/src/views/GraphView.spec.ts` (o extensión del spec de `graphUtils`)

## Files to Modify
- `frontend/src/views/GraphView.vue` — `label` por relación + toggle de visibilidad
- `frontend/src/components/ui/GraphFilters.vue` / `frontend/src/components/graph/GraphToolbar.vue` — control de etiquetas
- `frontend/src/locales/en.json` / `es.json` — `graphExplorer.relations.*`
- `features.md` — §12

## Related Issues
- #53 (Dependency graph visualization), #80 (Graph visualization), #480–#482 (interactive editing/filters), #511 (interactive exploration & inspector), #517 (datos reales del grafo)
