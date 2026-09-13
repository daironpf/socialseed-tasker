# Issue #473: Add token consumption and cost metrics panel per agent

## Description
Add a cost audit module within `DashboardSystemView` and `IssueDetailView` showing token consumption breakdown by issue and agent.

## Expected Behavior
- Token breakdown per issue: Prompt tokens, Completion tokens, Estimated cost in USD by model
- SVG charts in system dashboard with daily/weekly cumulative consumption per AI agent
- Visual alerts when a task exceeds pre-set token budget
- Model-specific pricing table (Claude 3.5 Sonnet, GPT-4 Turbo, GPT-4o, etc.)

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Dashboard / Agent Metrics

## Changes Made
1. Created `modelPricing.ts` utility with 6 model pricing definitions (Claude 3.5 Sonnet, Claude 3 Opus, GPT-4 Turbo, GPT-4o, Gemini Pro, Llama 3)
2. Created `TokenMetrics.vue` component:
   - Token breakdown (prompt/completion/cost) per issue
   - Model and provider display
   - Budget progress bar with color coding (green/amber/red)
   - Budget exceeded alert badge
3. Created `AgentCostChart.vue` SVG chart component:
   - Daily cost consumption bar chart
   - Period selector (7D/30D/All)
   - Y-axis ticks with cost labels
   - X-axis date labels
   - Color-coded bars (green=low, amber=medium, red=high)
   - Total cost and tokens summary
4. Integrated TokenMetrics into IssueDetailView Progress tab
5. Integrated AgentCostChart into DashboardSystemView
6. Added estimated token calculation from agent log content
7. Added i18n keys for tokens UI (EN/ES)

## Verification
- IssueDetailView Progress tab shows token consumption metrics
- DashboardSystemView shows daily token consumption chart
- Budget exceeded indicator works correctly
- Model pricing applied correctly
- Chart period selector filters data
