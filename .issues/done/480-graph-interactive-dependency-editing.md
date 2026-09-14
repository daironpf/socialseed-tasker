# Issue #480: Interactive dependency editing in GraphView (Drag-to-Connect)

## Description
Allow creating blocking/dependency relationships by drawing connections directly between nodes on the graph canvas.

## Expected Behavior
- Edit mode toggle in GraphView ("*Connect Mode*")
- Drag from source node to destination node to open quick relationship modal (`BLOCKS`, `DEPENDS_ON`)
- Frontend cycle detection before API request
- Right-click on edge to delete connection
- Visual feedback during drag (ghost line from source to cursor)

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Graph / Interactive Editing

## Changes Made
1. Added "Connect" toggle button to GraphView toolbar
   - Blue highlight when active
   - Hint text "Click two nodes to connect"
   - Disables drag/pan when in connect mode
2. Created `RelationshipModal.vue`:
   - Shows from→to labels
   - Two relationship types: BLOCKS (red, 🛑) and DEPENDS_ON (blue, 🔗)
   - Selectable type cards with descriptions
   - Create/Cancel buttons
3. Created `graphUtils.ts`:
   - `wouldCreateCycle()` — DFS-based cycle detection before creating edge
   - Prevents circular dependencies
4. Updated GraphView network click handler:
   - First click selects source node
   - Second click on different node opens RelationshipModal
   - Cycle detection shows error toast
5. Cycle error display: bottom-center red toast with 3s auto-dismiss
6. Added i18n keys for graph relationships (EN/ES)

## Verification
- Toggle Connect mode on/off
- Click first node highlights it as source
- Click second node opens relationship modal
- Selecting BLOCKS or DEPENDS_ON and Create confirms
- Cycle attempt shows error message
- Connect mode disables node dragging
