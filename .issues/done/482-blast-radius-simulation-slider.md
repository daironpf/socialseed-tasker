# Issue #482: Add blast radius simulation slider in AnalysisView

## Description
Add an interactive simulator within `AnalysisView` to evaluate failure scope based on dependency depth.

## Expected Behavior
- Interactive slider for analysis depth (1 to 5 levels)
- Real-time visual recalculation in `ImpactSvgTree` when slider moves
- Numeric indicator of percentage of system affected relative to total components
- Slider debounced to avoid excessive recalculations
- Visual depth markers on the SVG tree

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Analysis / Blast Radius

## Changes Made
1. Created `BlastRadiusSlider.vue` component:
   - Range slider (1-5) with debounced input (200ms)
   - Depth value badge display
   - Affected percentage indicator with color-coded progress bar
   - Depth markers showing count per level (L1: 3, L2: 5, etc.)
   - Active/inactive state for depth markers
2. Updated ImpactAnalysisPanel:
   - Integrated BlastRadiusSlider above stats grid
   - Added `blastDepth` ref state
   - Computed `depthCounts` from impact result
   - Added componentsStore import for total component count
3. i18n keys for blast radius labels (EN/ES)

## Verification
- Slider moves from 1-5 with debounced updates
- Affected percentage calculates correctly
- Depth markers show count per level
- Progress bar color changes based on percentage (green/amber/red)
- Slider value badge updates in real-time
