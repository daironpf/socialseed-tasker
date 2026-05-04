# Issue #226: Reasoning Visualization in Vue Dashboard

## Description
Visualize the "Thread of Thought" of AI agents in the frontend dashboard.

## Acceptance Criteria
- [ ] New component `ReasoningGraph.vue`.
- [ ] Graphical representation of decisions linking to issues and code changes.
- [ ] Timeline view of agent actions.

## Technical Notes
- Connects to the `/api/v1/reasoning/history` endpoint.
- Uses D3.js or similar for graph visualization.
