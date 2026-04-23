# Issue #68: Add impact analysis endpoint for components

## Description

The system supports impact analysis for individual issues (`GET /api/v1/analyze/impact/{issue_id}`) but not for entire components. When a component is delayed or has breaking changes, there is no way to see the cascading impact across the project.

## Problem Found

During the ecommerce test, the impact analysis for `product-catalog` issue correctly showed 4 directly affected and 2 transitively affected issues. However, there is no equivalent endpoint to ask "what happens if the entire `product-catalog` component is delayed?"

## Impact

- Project managers cannot assess component-level risk
- No way to answer "which components are most critical to the project timeline?"
- Requires manual aggregation of all issue-level impact analyses

## Suggested Fix

- Add `GET /api/v1/analyze/component-impact/{component_id}`
- Traverse all issues in the component, compute combined impact graph
- Return: directly affected components, transitively affected components, total blocked issues, risk level
- Include a "criticality score" based on how many other components depend on this one

## Priority

MEDIUM

## Labels

api, feature, analysis
