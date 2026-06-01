# Issue #386: `POST /api/v1/agents/register` returns HTTP 500 INTERNAL_ERROR

## Description
Even with the correct API URL, the agent registration endpoint returns a 500 Internal Server Error with no useful detail. The underlying error is likely a missing or mismatched parameter in the Neo4j Cypher query (e.g., `createdAt` parameter).

## Expected Behavior
- Agent registration should return 201 with the created agent data
- Errors should include actionable details in the response

## Actual Behavior
```json
{
  "data": null,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "details": { "detail": null }
  }
}
```

## Steps to Reproduce
1. `$env:TASKER_API_URL="http://localhost:8888"`
2. `tasker agent register -i dev-agent-01 -n "Developer Agent" -r developer`
3. Observe: "Failed to register agent: ... INTERNAL_ERROR"

## Status: DONE

## Priority: MEDIUM

## Resolution
Fixed two bugs:
1. **`queries.` → `neo4j_queries.`**: The import at line 139 does `from socialseed_tasker.infrastructure import neo4j_queries` but all references used `queries.CREATE_AGENT_NODE` (missing `neo4j_` prefix). Same pattern in 5 other functions (specialize, list, etc.). Fixed all 7 occurrences with replaceAll.
2. **Missing `_agents` dict**: Module-level in-memory store `_agents: dict[str, Any] = {}` was never defined, causing `NameError` on first write in `register_agent()`. Added it at module scope before `agent_router`.

Agent registration now returns HTTP 201 with correct agent data.
