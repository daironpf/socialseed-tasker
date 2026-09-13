# Issue #480: Interactive dependency editing in GraphView (Drag-to-Connect)

## Description
Allow creating blocking/dependency relationships by drawing connections directly between nodes on the graph canvas.

## Expected Behavior
- Edit mode toggle in GraphView ("*Connect Mode*")
- Drag from source node to destination node to open quick relationship modal (`BLOCKS`, `DEPENDS_ON`)
- Frontend cycle detection before API request
- Right-click on edge to delete connection
- Visual feedback during drag (ghost line from source to cursor)

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Graph / Interactive Editing

## Implementation Plan
1. Add edit mode toggle to GraphView toolbar
2. Implement drag-to-connect interaction on vis-network
3. Create `RelationshipModal.vue` for quick relationship creation
4. Implement cycle detection algorithm in frontend
5. Add right-click context menu for edge deletion
6. Visual drag feedback with ghost line
7. Add i18n keys for relationship types

## Acceptance Criteria
- [ ] Edit mode toggle available
- [ ] Drag from node to node opens relationship modal
- [ ] Modal offers BLOCKS and DEPENDS_ON options
- [ ] Cycle detection prevents circular dependencies
- [ ] Right-click on edge shows delete option
- [ ] Ghost line during drag
- [ ] i18n support

## Verification
- Toggle edit mode on
- Drag from issue A to issue B
- Modal appears for relationship type
- Selecting BLOCKS creates dependency
- Cycle attempt shows error
- Right-click edge shows delete option

## Related Issues
- #481 (Sub-graph filtering)
