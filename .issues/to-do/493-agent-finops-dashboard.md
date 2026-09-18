# Issue #493: Create Enterprise Agent FinOps and ROI Analytics Dashboard

## Description
Organisations need complete visibility into token spending and return on investment across multiple AI models (Claude 3.5 Sonnet, GPT-4o, DeepSeek). The existing TokenMetrics needs expansion into a full FinOps dashboard.

## Expected Behavior
- Overall ROI cards comparing "Token Cost ($) vs Estimated Human Hours Saved"
- Cost heatmap grouped by component, task, and model
- Budget Guardrail Alerts: Visual indicators when an issue exceeds $5.00 in LLM execution costs
- Project and organizational cost caps controls

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Analytics / FinOps

## Implementation Plan
1. Create `AgentFinOpsView.vue` full-page dashboard
2. Build ROI comparison cards (cost vs human hours)
3. Implement cost heatmap (component, task, model dimensions)
4. Add budget guardrail alerts ($5 threshold)
5. Build project/org cost caps controls
6. Create FinOps-specific types and store
7. Add i18n keys for FinOps dashboard
8. Add navigation route in Analysis section

## Acceptance Criteria
- [ ] ROI cards: Token Cost vs Human Hours Saved
- [ ] Cost heatmap by component, task, model
- [ ] Budget guardrail alerts at $5
- [ ] Project cost caps controls
- [ ] Organizational cost caps controls
- [ ] Export capability
- [ ] i18n support

## Verification
- Navigate to Agent FinOps Dashboard
- See ROI comparison cards
- View cost heatmap with all dimensions
- Trigger budget alert by exceeding $5
- Set project cost cap
- Set organizational cost cap
- Export report

## Related Issues
- #492 (Code Graph Overlay), #494 (Auto-Healing Monitor)
