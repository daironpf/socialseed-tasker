# Issue #473: Add token consumption and cost metrics panel per agent

## Description
Add a cost audit module within `DashboardSystemView` and `IssueDetailView` showing token consumption breakdown by issue and agent.

## Expected Behavior
- Token breakdown per issue: Prompt tokens, Completion tokens, Estimated cost in USD by model
- SVG charts in system dashboard with daily/weekly cumulative consumption per AI agent
- Visual alerts when a task exceeds pre-set token budget
- Model-specific pricing table (Claude 3.5 Sonnet, GPT-4 Turbo, GPT-4o, etc.)

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Dashboard / Agent Metrics

## Implementation Plan
1. Create `TokenMetrics.vue` component for per-issue breakdown
2. Create `AgentCostChart.vue` SVG chart for dashboard
3. Implement token budget threshold alerts
4. Add model pricing constants
5. Integrate into DashboardSystemView and IssueDetailView
6. Add API endpoint for token usage data

## Acceptance Criteria
- [ ] Token breakdown (prompt/completion/cost) per issue displayed
- [ ] SVG chart showing daily/weekly consumption per agent
- [ ] Visual alert when token budget exceeded
- [ ] Model-specific pricing applied correctly
- [ ] i18n support

## Verification
- IssueDetailView shows token count and cost for agent logs
- Dashboard shows consumption chart
- Alert appears when budget exceeded
- Costs calculated correctly per model

## Related Issues
- #472 (Agent streaming)
