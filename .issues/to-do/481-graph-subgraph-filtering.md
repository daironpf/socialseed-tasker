# Issue #481: Add sub-graph filtering by component/module in GraphView

## Description
Improve graph navigability by allowing isolation of specific modules to avoid visual spaghetti.

## Expected Behavior
- Multi-select dropdown of components in GraphView toolbar
- "Direct dependencies only" mode: hide nodes more than N hops away from selected component
- Dynamic layout recalculation (force-directed / hierarchical) when filters applied
- Component filter persists in URL query params
- Reset filter button

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Graph / Filtering

## Implementation Plan
1. Create `GraphFilters.vue` toolbar component
2. Implement multi-select component dropdown
3. Add "max hops" slider (1-5)
4. Implement sub-graph filtering logic on vis-network data
5. Trigger layout recalculation on filter change
6. Sync filters to URL query params
7. Add i18n keys for filter labels

## Acceptance Criteria
- [ ] Multi-select component dropdown
- [ ] Max hops slider (1-5)
- [ ] Sub-graph filtering hides distant nodes
- [ ] Layout recalculates on filter change
- [ ] Filters synced to URL
- [ ] Reset filter button
- [ ] i18n support

## Verification
- Select specific component in filter
- Graph shows only related nodes within N hops
- Layout adjusts automatically
- URL reflects filter state
- Reset button clears filters

## Related Issues
- #480 (Interactive editing)
