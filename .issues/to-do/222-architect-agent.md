# Issue #222: Autonomous Architect Agent for Rule Enforcement

## Description
Implement a specialized Agent role that automatically reviews proposed changes against architectural constraints.

## Acceptance Criteria
- [ ] Agent role `ARCHITECT` logic implementation.
- [ ] Integration with `tasker.constraints.yml`.
- [ ] Validation of `core/` imports to ensure no framework leakage.
- [ ] Automatic "Veto" if constraints are violated.

## Technical Notes
- Uses `Code-as-Graph` to analyze imports without reading files.
- Can be triggered as a "pre-commit" or "pre-push" agent workflow.
