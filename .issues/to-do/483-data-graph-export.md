# Issue #483: Add data and graph export module (CSV, JSON, SVG)

## Description
Allow downloading reports and visual diagrams for management consumption or external audits.

## Expected Behavior
- Export ListView table to CSV and JSON respecting active filters
- Export GraphView and ImpactSvgTree as SVG or high-res PNG
- Export ConstraintsView violations report as Markdown/PDF summary
- Export button in each relevant view's toolbar
- Loading state during export generation

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Export / Data

## Implementation Plan
1. Create `useExport` composable with CSV, JSON, SVG, PNG export methods
2. Implement CSV export with filter respect for ListView
3. Implement SVG/PNG export using `html-to-image` or similar
4. Implement Markdown report generation for constraints
5. Add export buttons to relevant view toolbars
6. Add loading states during export
7. Add i18n keys for export labels

## Acceptance Criteria
- [ ] CSV export for ListView with active filters
- [ ] JSON export for ListView with active filters
- [ ] SVG/PNG export for GraphView
- [ ] SVG/PNG export for ImpactSvgTree
- [ ] Markdown report for ConstraintsView violations
- [ ] Export buttons in view toolbars
- [ ] Loading state during generation
- [ ] i18n support

## Verification
- Export ListView to CSV - file downloads with correct data
- Export GraphView to PNG - high-res image produced
- Export constraints to Markdown - readable report generated
- Active filters reflected in exported data
- Loading spinner shown during export

## Related Issues
- #482 (Blast radius slider)
