# Issue #72: Add project summary dashboard endpoint

## Description

There is no single endpoint that gives an overview of a project: total issues by status, issues by priority, dependency health, blocked vs workable count, and component breakdown.

## Problem Found

To get a project overview during the ecommerce test, multiple API calls were needed: list issues, list components, check blocked issues, run impact analysis. There is no aggregated summary.

## Impact

- Dashboards must aggregate data from multiple endpoints
- No quick way to answer "how is my project doing?"
- Project managers cannot get a snapshot without custom tooling

## Suggested Fix

- Add `GET /api/v1/projects/{project_name}/summary` endpoint
- Return:
  - `total_issues`, `by_status: {OPEN: N, IN_PROGRESS: N, CLOSED: N}`, `by_priority: {CRITICAL: N, ...}`
  - `components_count`, `blocked_issues_count`, `workable_issues_count`
  - `dependency_health`: percentage of issues with resolved dependencies
  - `top_blocked_components`: components with most blocked issues
  - `critical_path`: longest dependency chain in the project

## Priority

MEDIUM

## Labels

api, feature, dashboard
