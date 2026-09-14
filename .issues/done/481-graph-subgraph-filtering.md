# Issue #481: Add sub-graph filtering by component/module in GraphView

## Description
Improve graph navigability by allowing isolation of specific modules to avoid visual spaghetti.

## Expected Behavior
- Multi-select dropdown of components in GraphView toolbar
- "Direct dependencies only" mode: hide nodes more than N hops away from selected component
- Dynamic layout recalculation (force-directed / hierarchical) when filters applied
- Component filter persists in URL query params
- Reset filter button

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Graph / Filtering

## Changes Made
1. Created `GraphFilters.vue` toolbar component:
   - Multi-select component dropdown with checkboxes
   - Max hops slider (1-5) with value display
   - Reset button when filters active
   - Selected count badge
   - Teleported dropdown with clear all option
2. Updated GraphView graphData computed:
   - BFS-based node reachability calculation from selected components
   - Includes issues belonging to selected components within maxHops
   - Filters both nodes and edges based on visibility
   - Adjacency list built for dependency traversal
3. Added watch on selectedComponents and maxHops to trigger layout recalculation
4. Integrated GraphFilters into GraphView toolbar between layout buttons and connect mode
5. Added i18n keys for filter labels (EN/ES)

## Verification
- Select specific component in filter dropdown
- Graph shows only related nodes within N hops
- Max hops slider adjusts visible scope
- Layout recalculates automatically on filter change
- Reset button clears all filters
- Component count updates in button label
