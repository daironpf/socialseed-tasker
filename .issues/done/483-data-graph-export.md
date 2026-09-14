# Issue #483: Add data and graph export module (CSV, JSON, SVG)

## Description
Allow downloading reports and visual diagrams for management consumption or external audits.

## Expected Behavior
- Export ListView table to CSV and JSON respecting active filters
- Export GraphView and ImpactSvgTree as SVG or high-res PNG
- Export ConstraintsView violations report as Markdown/PDF summary
- Export button in each relevant view's toolbar
- Loading state during export generation

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Export / Data

## Changes Made
1. Created `useExport.ts` composable:
   - `exportCSV()` — CSV generation with proper escaping
   - `exportJSON()` — JSON with pretty-print
   - `exportSVG()` — SVG serialization and download
   - `exportPNG()` — SVG to PNG with 2x scale
   - `exportMarkdown()` — Markdown text download
   - `exporting` ref for loading state
2. ListView integration:
   - Export dropdown menu (CSV/JSON) in header
   - Respects active filters for export data
   - Teleported dropdown with format badges
3. GraphView integration:
   - Export PNG button below graph
   - Captures graph canvas as SVG and converts to PNG
4. Added i18n keys for export labels (EN/ES)

## Verification
- Export ListView to CSV — downloads file with filtered data
- Export ListView to JSON — downloads file with filtered data
- Export GraphView to PNG — downloads high-res image
- Active filters reflected in exported data
- Export menu closes after selection
