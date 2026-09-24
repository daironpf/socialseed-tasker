# Issue #511: Interactive Graph Visualization with Mock Graph Exploration & Filters

## Description

La visualización del grafo de dependencias y causa raíz es la ventaja competitiva central de Tasker. La vista actual del grafo simulado (`GraphView` + vis-network) debe ser altamente interactiva y ofrecer herramientas avanzadas de exploración empresarial.

Origen: `notas.md` → Issue #503 (renumerada a #511; #503 ya está en done).

## Status: DONE

> Resuelto: toolbar de exploración (`GraphToolbar.vue`: zoom in/out/fit, toggle de clustering por componente con `network.cluster` + `openCluster` al clicar, trazado de ruta origen→destino con selects y resaltado ámbar + atenuado del resto). Filtros extendidos en `GraphFilters.vue` (prioridad CRITICAL/HIGH/MEDIUM/LOW y tipo de nodo Issue/Component/Agent/Policy/PR como pills). Nodos mock nuevos en `GraphView`: agentes desde `usersStore` (rombo naranja, aristas a issues asignados), políticas desde `policiesStore` (estrella rosa) y PRs de `issue.github_sync` (cuadrado gris, arista issue→PR); leyenda actualizada. Inspector lateral `NodeInspector.vue` al clicar nodo/arista: metadatos, blast-radius (total/directo/depth/críticos/high vía `graphUtils.blastRadius`), enlaces rápidos (abrir issue, rutas, URL de GitHub) y, para aristas, relación/dirección/peso/detección de ciclo vía `findPath`. `graphUtils.ts` ampliado con `findPath` (BFS dirigido + inverso) y `blastRadius`. Sección i18n `graphExplorer` (60 claves, EN+ES). Conect mode, cycle detection y code overlay intactos. `npm run build` OK.

## Priority: HIGH

## Component
Frontend / Graph / Visualization / Exploration

## Type
feat / visualization

## Implementation
1. **Controles de exploración:**
   - Zoom in/out, pan, centrado automático (fit) en toolbar de `GraphView`
   - Agrupación por clusters/módulos (componentes o paquetes mock)
   - Trazado de rutas de impacto: resaltar camino origen → destino (reutilizar `graphUtils` BFS)

2. **Filtros dinámicos de nodos:**
   - Por criticidad (prioridad de issues)
   - Por tipo de nodo: Issue, Component, Agent, Policy, Pull Request
   - Extender `GraphFilters.vue` + `codeGraphStore`/`issuesStore` para tipos nuevos (Agent/Policy/PR como nodos mock)

3. **Inspector lateral de nodos/aristas:**
   - Al clicar nodo o arista: panel lateral con metadatos mock completos
   - Métricas de blast-radius (nodos alcanzados, depth, severidad)
   - Enlaces rápidos a componentes/issues relacionados (navegación a detalle)
   - Al clicar arista: tipo de relación, peso, dirección, detección de ciclo

4. **Mock enrichment:**
   - Añadir nodos Agent/Policy/PR de prueba en dataset de dependencias o `codeGraph`
   - Mantener toggle de Code Overlay (#492) coherente con nuevos tipos

## Acceptance Criteria
- [x] Zoom, pan, auto-center controls work on GraphView
- [x] Cluster/module grouping toggle works
- [x] Impact path tracing highlights routes between selected nodes
- [x] Dynamic filters by criticality and node type (Issue, Component, Agent, Policy, Pull Request)
- [x] Side inspector shows full mock metadata, blast-radius metrics, and quick links on node/edge click
- [x] Existing connect mode, cycle detection, and code overlay still work
- [x] i18n support (EN + ES)
- [x] `npm run build` passes

## Files to Create
- `frontend/src/components/graph/GraphToolbar.vue` (zoom/pan/fit/cluster controls)
- `frontend/src/components/graph/NodeInspector.vue`
- `frontend/src/types/graphExplorer.ts` (optional)

## Files to Modify
- `frontend/src/views/GraphView.vue` — toolbar, inspector wiring, path highlight
- `frontend/src/components/ui/GraphFilters.vue` — criticality + node type filters
- `frontend/src/stores/codeGraphStore.ts` / `issuesStore.ts` — node type sets
- `frontend/src/utils/graphUtils.ts` — impact path helpers if needed
- `frontend/dataset-de-pruebas/dependencies.json` — optional Agent/Policy/PR nodes
- `frontend/src/locales/en.json` / `es.json` — graphExplorer keys
- `features.md` — when done

## Related Issues
- #80 (Graph Visualization), #480 (Interactive Dependency Editing), #481 (Subgraph Filtering), #482 (Blast Radius Slider), #492 (Code Graph Overlay), #13 (Impact & Root Cause Analysis)
