# Issue #490: Develop Interactive Architectural Policy Sandbox

## Description
Users need a way to test Cypher-based architectural constraints before enforcing them live in Neo4j. An interactive playground is needed to draft rules and run dry-run simulations.

## Expected Behavior
- Code/YAML editor for drafting new constraint rules (e.g., layer separation policies)
- "Simulate Policy" button to execute dry-runs against Neo4j
- Visual impact report detailing which existing or proposed graph edges violate the rule
- One-click option to promote a simulated rule into active enforcement

## Status: PENDING

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
- [ ] Code/YAML editor for constraint rules
- [ ] Simulate Policy button with dry-run
- [ ] Visual impact report of violating edges
- [ ] Promote to Active button
- [ ] Error handling for invalid rules
- [ ] i18n support

## Verification
- Navigate to Policy Sandbox
- Write a constraint rule in editor
- Click Simulate - see impact report
- Review violating edges in visual display
- Click Promote - rule becomes active
- Invalid rules show error messages

## Related Issues
- #489 (HITL Command Center), #491 (Graph RAG Explorer)
