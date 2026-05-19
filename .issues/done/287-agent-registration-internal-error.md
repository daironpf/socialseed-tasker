# Issue #287: Agent Registration API Returns INTERNAL_ERROR

## Description
When attempting to register an agent via the Tasker API endpoint `POST /api/v1/agents/register`, the system returns an `INTERNAL_ERROR` due to a missing parameter in the Neo4j Cypher query. The error occurs because the query expects a parameter named `createdAt` but the code is passing a parameter with a different name or missing entirely.

## Expected Behavior
- Agent registration should succeed with a 201 status code
- The agent node should be created in Neo4j with all required properties
- Response should include the created agent data

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

## Technical Analysis

### Error Trace
```
neo4j.exceptions.ClientError:
  {neo4j_code: Neo.ClientError.Statement.ParameterMissing}
  {message: Expected parameter(s): createdAt}
  {gql_status: 50N42}
```

### Problem Location
- **File**: `src/socialseed_tasker/entrypoints/web_api/routes.py`
- **Function**: `register_agent` (line ~4014)
- **Query**: `queries.CREATE_AGENT_NODE`

### Root Cause
The Cypher query in `queries.py` line 227 expects:
```cypher
SET a.createdAt = $createdAt
```

But the routes.py code at line 4046 passes:
```python
createdAt=agent_data["created_at"],
```

The parameter name mismatch causes Neo4j to reject the query with `ParameterMissing`.

## Steps to Reproduce
1. Start Tasker services: `cd .agent/tasker && docker compose up -d`
2. Send registration request:
```bash
curl -X POST "http://127.0.0.1:8888/api/v1/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "name": "Test Agent",
    "role": "developer",
    "capabilities": ["coding"]
  }'
```
3. Observe `INTERNAL_ERROR` in response

## Component
API - Agent Registration Endpoint

## Status: TODO

## Priority: CRITICAL

## Technical Implementation

### Option 1: Fix Query Parameter Name
Change the Cypher query parameter from `$createdAt` to `$created_at` to match the code:
```python
# In routes.py line 4046
session.run(
    queries.CREATE_AGENT_NODE,
    id=body.agent_id,
    name=body.name,
    role=body.role,
    status="idle",
    capabilities=", ".join(body.capabilities) if body.capabilities else "",
    created_at=agent_data["created_at"],  # Changed from createdAt
)
```

And update `queries.py`:
```cypher
SET a.createdAt = $created_at
```

### Option 2: Standardize on camelCase
Change the code to use `createdAt` consistently everywhere.

## Acceptance Criteria
- [ ] Agent registration returns 201 status code
- [ ] Agent node is created in Neo4j with all properties
- [ ] Response includes created agent data
- [ ] Unit test verifies agent registration works

## Impact
- **Blocking**: AI agents cannot register with Tasker
- **Affected Features**: Agent coordination, tracking, specialization, dispatching
- **Workaround Available**: No

## Related Issues
- Issue #288: Policy Node Severity Property Warning (separate but related warning)