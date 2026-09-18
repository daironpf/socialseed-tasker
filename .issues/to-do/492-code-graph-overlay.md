# Issue #492: Integrate Tree-Sitter Code Structure Overlay into GraphView

## Description
Linking code structure (Files, Classes, Functions) with task issues in Neo4j gives deep visibility into exact code areas affected by an agent. A toggleable "Code Overlay" layer is needed in the dependency graph.

## Expected Behavior
- Toggle control to show/hide AST code nodes (File, Class, Function) alongside Issue nodes
- Distinct visual styling for code nodes vs task nodes
- Highlighted edges showing real-time agent access: `(Issue)-[:AFFECTS]->(Function)`

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Graph / Code Overlay

## Implementation Plan
1. Add toggle control to `GraphView.vue` for Code Overlay
2. Create `CodeGraphOverlay.vue` component
3. Fetch code structure data from `GET /graph/code-structure`
4. Render AST nodes (File, Class, Function) with distinct styling
5. Highlight `AFFECTS` edges for agent access
6. Implement node click interactions
7. Add i18n labels for overlay controls
8. Integrate with existing graph filters

## Acceptance Criteria
- [ ] Toggle to show/hide code nodes
- [ ] Distinct styling: code nodes vs task nodes
- [ ] File, Class, Function node types
- [ ] Highlighted AFFECTS edges
- [ ] Click code node shows details
- [ ] Integrates with existing graph filters
- [ ] i18n support

## Verification
- Navigate to Graph View
- Toggle Code Overlay on
- See AST nodes alongside issue nodes
- Code nodes have distinct styling
- AFFECTS edges highlighted
- Click code node shows details
- Toggle off hides code nodes

## Related Issues
- #491 (Graph RAG Explorer), #493 (Agent FinOps)
