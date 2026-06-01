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

## Status: PENDING

## Priority: MEDIUM
