# Issue #528: Graph View — etiquetas explícitas de aristas

## Description

`GraphView` dibuja las relaciones como flechas sin etiqueta: los tipos (`relation: 'dependency' | 'component' | 'agent' | ...`) solo se muestran al inspeccionar la arista en el `Edge inspector`. La ÉPICA 2 de `notas.md` exige "dibujar bordes con etiquetas explícitas: `DEPENDS_ON`, `BLOCKS`, `AFFECTS` y `BELONGS_TO`". El resto del visualizador (nodos Issue/Component, filtros por estado y componente, zoom/pan/drag, panel lateral al clicar) ya está implementado (#53, #80, #511): esta issue cubre solo el gap de etiquetas.

Origen: `notas.md` → ÉPICA 2 · Issue #5 (→ #528).

## Status: DONE (2026-09-30)

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
- [x] Cada arista muestra su tipo como etiqueta visible (`DEPENDS_ON`, `BLOCKS`, `AFFECTS`, `BELONGS_TO`)
- [x] Toggle para mostrar/ocultar etiquetas sin recargar el grafo
- [x] Leyenda e inspector de aristas consistentes con las etiquetas mostradas
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Files to Create
- `frontend/src/utils/graphUtils.spec.ts` (spec nuevo: `edgeRelationLabel`, `edgeRelationColor`, `EDGE_RELATION_COLORS`, `buildBlocksEdges`)

## Files to Modify
- `frontend/src/views/GraphView.vue` — `label` + `font` (color por tipo, size 10) por relación en cada arista; aristas inversas `BLOCKS` desde `issue.blocks` (curva `curvedCCW` para separarlas de `DEPENDS_ON`); código overlay separa `AFFECTS` vs `CODE_REFERENCE`; leyenda de tokens de relación en la cabecera; `showEdgeLabels` + `toggleEdgeLabels()` (aplica/limpia labels vía `DataSet.update()` sin rebuild)
- `frontend/src/components/graph/GraphToolbar.vue` — botón toggle de etiquetas (prop `showLabels`, emit `update:showLabels`)
- `frontend/src/utils/graphUtils.ts` — `EDGE_RELATION_COLORS`, `edgeRelationLabel()`, `edgeRelationColor()`, `buildBlocksEdges()`
- `frontend/src/types/graphExplorer.ts` — `EdgeRelation` + `blocks` + `affects`
- `frontend/src/locales/en.json` / `es.json` — `graphExplorer.relations.*` (tokens `DEPENDS_ON`/`BLOCKS`/`AFFECTS`/`BELONGS_TO`/`CODE_REFERENCE`/`ASSIGNED_TO`/`LINKED_TO_PR`, mismos EN+ES) + `edgeLabels`/`edgeLabelsOn`
- `features.md` — §12

## Verification (2026-09-30)
- Decisión de diseño: `BLOCKS` se dibuja como arista inversa (`issue.blocks` = dependientes del issue, `LIST_ISSUES` de Neo4j) solo cuando ni el bloqueante ni el bloqueado están `CLOSED` (una dependencia cerrada ya no causa bloqueo); la arista `DEPENDS_ON` original se mantiene (curvas `curvedCCW` separan ambas).
- `npm run lint` → 0 errores (2 warnings preexistentes en `IssueDetailView.vue`)
- `npm test` → 178/178 (167 base + 11 nuevos en `graphUtils.spec.ts`)
- `npm run build` (vue-tsc + vite) → verde
- Docker: `docker compose build tasker-board && docker compose up -d tasker-board` → tasker-board responde 200 en :19001; API real devuelve `blocks` poblado en `/api/v1/issues` (valida que se rendericen aristas `BLOCKS`)
- Smoke Playwright headless sobre :19001 (script temporal, no commiteado): leyenda muestra `DEPENDS_ON`/`BLOCKS`/`BELONGS_TO` (+ `AFFECTS`/`CODE_REFERENCE` al activar Code Overlay, + `ASSIGNED_TO`/`LINKED_TO_PR`); toggle `Edge labels visible` ↔ `Show edge labels` sin errores de consola; capturas confirman labels dibujados en el canvas (`DEPENDS_ON`, `BELONGS_TO`, `LINKED_TO_PR`, `ASSIGNED_TO`); dataset mock contiene 7 aristas `BLOCKS` válidas tras las reglas de estado; 0 `pageerror`.
- Glitch preexistente verificado (diferencial contra `98ff767` en worktree temporal): al activar Code Overlay el canvas queda ~4s en blanco y se autorecupera a los ~5s (zoom→toggle de layout no lo sufren). Idéntico antes y después de #528 — no es regresión de esta issue.

## Related Issues
- #53 (Dependency graph visualization), #80 (Graph visualization), #480–#482 (interactive editing/filters), #511 (interactive exploration & inspector), #517 (datos reales del grafo)
