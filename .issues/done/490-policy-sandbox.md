# Issue #490: Develop Interactive Architectural Policy Sandbox

## Description
Users need a way to test Cypher-based architectural constraints before enforcing them live in Neo4j. An interactive playground is needed to draft rules and run dry-run simulations.

## Expected Behavior
- Code/YAML editor for drafting new constraint rules (e.g., layer separation policies)
- "Simulate Policy" button to execute dry-runs against Neo4j
- Visual impact report detailing which existing or proposed graph edges violate the rule
- One-click option to promote a simulated rule into active enforcement

## Status: DONE

## Priority: HIGH

## Component
Frontend / Constraints / Policy Sandbox

## Implementation Plan
1. Create `PolicySandbox.vue` component in constraints module
2. Integrate code/YAML editor for rule drafting
3. Implement "Simulate Policy" button with dry-run API call
4. Build visual impact report showing violating edges
5. Add "Promote to Active" one-click button
6. Create sandbox-specific types and store
7. Add i18n keys for sandbox labels
8. Add navigation to Constraints section

## Acceptance Criteria
- [x] Code/YAML editor for constraint rules
- [x] Simulate Policy button with dry-run
- [x] Visual impact report of violating edges
- [x] Promote to Active button
- [x] Error handling for invalid rules
- [x] i18n support (EN + ES)

## Verification
- Navigate to Policy Sandbox
- Write a constraint rule in editor
- Click Simulate - see impact report
- Review violating edges in visual display
- Click Promote - rule becomes active
- Invalid rules show error messages

## Files Created
- `frontend/src/types/sandbox.ts` — SandboxRule, SimulationResult, SandboxMetrics types
- `frontend/src/stores/sandboxStore.ts` — Pinia store with 4 mock rules, 2 mock simulations, CRUD + simulate + promote
- `frontend/src/views/PolicySandboxView.vue` — Main view with metrics, rule list, code editor, impact report
- `frontend/src/components/sandbox/ImpactReport.vue` — Visual impact report with violations list

## Files Modified
- `frontend/src/router/index.ts` — Added `/sandbox` route
- `frontend/src/components/layout/Sidebar.vue` — Added "Policy Sandbox" nav item
- `frontend/src/components/layout/AppHeader.vue` — Added header title mapping
- `frontend/src/locales/en.json` — Added 45 sandbox i18n keys
- `frontend/src/locales/es.json` — Added 45 sandbox i18n keys (Spanish)

## Related Issues
- #489 (HITL Command Center), #491 (Graph RAG Explorer)
