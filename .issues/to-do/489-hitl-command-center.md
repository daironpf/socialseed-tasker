# Issue #489: Build Unified HITL (Human-in-the-Loop) Approval Command Center

## Description
Autonomous agents request architectural changes or code refactors that require human authorization before execution. A unified HITL inbox is needed for quick review and approval.

## Expected Behavior
- Unified inbox listing pending approval requests from agents
- Split view integrating code diffs (`DiffViewer.vue`) and structural blast radius (`ImpactAnalysisPanel.vue`)
- One-click action buttons: "Approve", "Reject", and "Request Modifications" with feedback input
- Filter pending requests by severity, component, or agent ID

## Status: PENDING

## Priority: HIGH

## Component
Frontend / HITL / Command Center

## Implementation Plan
1. Create `HITLCommandCenter.vue` unified inbox view
2. Build pending approval request list with filtering
3. Implement split view: DiffViewer + ImpactAnalysisPanel
4. Add Approve/Reject/Request Modifications action buttons
5. Add feedback input for modifications
6. Implement severity, component, agent ID filters
7. Create HITL-specific types and store
8. Add i18n keys and navigation route

## Acceptance Criteria
- [ ] Unified inbox with pending approval requests
- [ ] Split view: code diffs + blast radius
- [ ] Approve button with confirmation
- [ ] Reject button with feedback input
- [ ] Request Modifications with detailed feedback
- [ ] Filter by severity, component, agent ID
- [ ] i18n support

## Verification
- Navigate to HITL Command Center
- See list of pending approval requests
- Click request to see split view (diff + impact)
- Approve action processes request
- Reject action with feedback processes request
- Filters narrow down the list

## Related Issues
- #488 (MCP Inspector), #490 (Policy Sandbox)
