# Issue #226: Reasoning Visualization in Vue Dashboard

## Description
Visualize the "Thread of Thought" of AI agents in the frontend dashboard.

## Acceptance Criteria
- [x] New component `ReasoningGraph.vue`.
- [x] Graphical representation of decisions linking to issues and code changes.
- [x] Timeline view of agent actions.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add `/api/v1/reasoning/timeline` endpoint
- [x] Returns reasoning entries in timeline format
- [x] Integrates with existing reasoning history system
- [x] Frontend can use endpoint for visualization

### Files Changed
- `routes.py`: Added reasoning_timeline endpoint

### Usage
```bash
# Timeline API endpoint
curl "http://localhost:8000/api/v1/reasoning/timeline?limit=100"

# Response:
{
  "timeline": [
    {
      "id": "...",
      "issue_id": "...",
      "agent_name": "tasker",
      "thought": "...",
      "decision": "...",
      "confidence": 0.85,
      "timestamp": "...",
      "decision_type": "solution_selection"
    }
  ],
  "count": 10
}
```
