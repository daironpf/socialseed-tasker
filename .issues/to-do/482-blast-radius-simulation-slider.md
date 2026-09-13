# Issue #482: Add blast radius simulation slider in AnalysisView

## Description
Add an interactive simulator within `AnalysisView` to evaluate failure scope based on dependency depth.

## Expected Behavior
- Interactive slider for analysis depth (1 to 5 levels)
- Real-time visual recalculation in `ImpactSvgTree` when slider moves
- Numeric indicator of percentage of system affected relative to total components
- Slider debounced to avoid excessive recalculations
- Visual depth markers on the SVG tree

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Analysis / Blast Radius

## Implementation Plan
1. Create `BlastRadiusSlider.vue` component
2. Implement depth parameter in impact analysis API call
3. Add debounced recalculation on slider change
4. Display affected percentage indicator
5. Add depth markers to ImpactSvgTree
6. Integrate into AnalysisView Impact tab
7. Add i18n keys for depth labels

## Acceptance Criteria
- [ ] Slider with depth 1-5
- [ ] Real-time SVG tree update on slider change
- [ ] Affected percentage indicator displayed
- [ ] Debounced to avoid excessive API calls
- [ ] Depth markers on SVG tree
- [ ] i18n support

## Verification
- Move slider to depth 1 - shows only direct dependencies
- Move slider to depth 3 - shows transitive dependencies
- Percentage indicator updates correctly
- SVG tree rebuilds smoothly
- Debounce prevents rapid API calls

## Related Issues
- #483 (Export data)
