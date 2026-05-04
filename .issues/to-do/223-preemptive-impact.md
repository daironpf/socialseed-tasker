# Issue #223: Pre-emptive Impact Analysis during Issue Creation

## Description
Analyze the potential risk of an issue at the moment it is created by linking it to a component and its code graph.

## Acceptance Criteria
- [ ] Automatic impact calculation on `issue create`.
- [ ] Risk score (LOW/MEDIUM/HIGH) based on call graph depth of the component.
- [ ] Warning if an issue affects "Hot Files" (frequently modified or highly coupled).

## Technical Notes
- Links the `Component` to its `CodeFile` nodes in the graph.
- Uses `ImpactAnalysis` service.
