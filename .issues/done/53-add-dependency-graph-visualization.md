# Issue #53: Add dependency graph visualization component

## Description

Create a visual graph representation showing the dependency relationships between issues using a node-link diagram.

### Requirements

- Create `frontend/src/components/graph/DependencyGraph.vue`
- Render a force-directed or hierarchical graph showing:
  - Nodes = issues (colored by status)
  - Edges = DEPENDS_ON relationships (arrows)
  - BLOCKS relationships (different edge style)
  - AFFECTS relationships (dotted edges)
- Clicking a node opens the issue detail panel
- Highlight the selected issue and its direct connections
- Zoom and pan support
- Legend explaining node colors and edge types
- Fallback: if graph library is too heavy, use a simplified SVG tree visualization

### Technical Details

- Use a lightweight graph library like `vis-network` or `d3-force` (prefer vis-network for simplicity)
- Or implement a simple SVG-based force layout from scratch if dependencies are a concern
- Data sourced from issuesStore
- Should handle up to ~100 issues without performance issues
- Responsive sizing

### Expected File Paths

- `frontend/src/components/graph/DependencyGraph.vue`
- `frontend/src/views/GraphView.vue` (optional dedicated view)

### Business Value

A visual graph makes it immediately obvious which issues are blocked, which are critical path items, and the overall structure of dependencies - something hard to see in lists or boards.

## Status: COMPLETED
