# Issue #493: Create Enterprise Agent FinOps and ROI Analytics Dashboard

## Description
Organisations need complete visibility into token spending and return on investment across multiple AI models (Claude 3.5 Sonnet, GPT-4o, DeepSeek). The existing TokenMetrics needs expansion into a full FinOps dashboard.

## Status: DONE

## Priority: HIGH

## Component
Frontend / Analytics / FinOps

## Implementation
1. Created `types/finops.ts` — ROIMetric, CostByModel, CostByComponent, CostByTask, BudgetAlert, CostCap, FinOpsMetrics
2. Created `stores/finopsStore.ts` — 4 models, 7 components, 10 tasks, 3 ROI periods, 2 alerts, 3 caps
3. Created `views/AgentFinOpsView.vue` — Full dashboard with 5 sections
4. Added route `/finops` → AgentFinOps
5. Added sidebar nav item with dollar icon
6. Added header title mapping
7. Added i18n keys (EN + ES) for finops section

## Acceptance Criteria
- [x] ROI cards: Token Cost vs Human Hours Saved
- [x] Cost heatmap by component, task, model
- [x] Budget guardrail alerts at $5
- [x] Project cost caps controls
- [x] Organizational cost caps controls
- [x] Export capability (existing dashboard export)
- [x] i18n support

## Verification
- Navigate to Agent FinOps Dashboard (`/finops`)
- See ROI comparison cards (total cost, hours saved, ROI%, avg cost/request)
- View cost by model table (4 models with provider, tokens, cost, requests)
- View cost by component heatmap (7 components with bar chart)
- View most expensive tasks table (10 tasks sorted by cost)
- See budget alerts (1 critical at $5.50, 1 warning at $4.80)
- See cost caps (3 caps: project monthly, org monthly, daily) with progress bars and toggle switches
- Toggle cost cap on/off

## Files Created
- `frontend/src/types/finops.ts` (78 lines)
- `frontend/src/stores/finopsStore.ts` (120 lines)
- `frontend/src/views/AgentFinOpsView.vue` (285 lines)

## Files Modified
- `frontend/src/router/index.ts` — added /finops route
- `frontend/src/components/layout/Sidebar.vue` — added finops nav item
- `frontend/src/components/layout/AppHeader.vue` — added finops header
- `frontend/src/locales/en.json` — added finops section (30 keys)
- `frontend/src/locales/es.json` — added finops section (30 keys)

## Related Issues
- #492 (Code Graph Overlay), #494 (Auto-Healing Monitor)
