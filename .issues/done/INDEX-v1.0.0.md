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

**Version:** 1.0.0  
**Focus:** Autonomous Agent Workflows & Ecosystem Health  
**Status:** COMPLETED

---

## Issue Index

| # | Issue | Priority | Status |
|---|---|---|---|
| #287 | Agent Registration API Returns INTERNAL_ERROR | CRITICAL | DONE |
| #288 | Policy Node Severity Property Warning | MEDIUM | DONE |
| #281 | Issue creation returns different ID formats | LOW | DONE |
| #280 | CLI help output shows truncated command descriptions | LOW | DONE |
| #279 | Cannot access API from Windows host | MEDIUM | DONE |
| #273 | Implement Issue RESOLVED_BY Commit Relationship | HIGH | DONE |
| #272 | Integrate Agent MUST_COMPLY_WITH Policy Validation | HIGH | DONE |
| #271 | Implement CodeSymbol CALLS Impact Analysis | HIGH | DONE |
| #270 | Implement Issue AFFECTS CodeSymbol Link | HIGH | DONE |
| #269 | Fix CamelCase Property Mappings in All Repositories | HIGH | DONE |
| #268 | Fix GET /api/v1/issues list endpoint KeyError | HIGH | DONE |
| #267 | [Final Issue in Done Folder] | - | - |
| #220 | Bidirectional Traceability | HIGH | DONE |
| #221 | RAG-Powered Phantom Dependency Detection | MEDIUM | DONE |
| #222 | Autonomous Architect Agent | HIGH | DONE |
| #223 | Pre-emptive Impact Analysis | HIGH | DONE |
| #224 | Self-Healing Documentation | MEDIUM | DONE |
| #225 | Autonomous Agent Workload Dispatcher | HIGH | DONE |
| #226 | Reasoning Visualization in Vue Dashboard | MEDIUM | DONE |
| #227 | Project Node Hierarchy | MEDIUM | DONE |
| #228 | RAG Embedding Storage Optimization | HIGH | DONE |
| #229 | Dynamic Internal Imports Relationship | MEDIUM | DONE |
| #230 | Code Graph Stale Node Pruning | HIGH | DONE |
| #231 | Agent Heartbeat Mechanism | HIGH | DONE |
| #232 | RAG Context Window Manager | MEDIUM | DONE |
| #246 | Implement Project Entity and Domain Model | HIGH | DONE |
| #247 | Align Neo4j Project Schema with v1.0 Documentation | HIGH | DONE |
| #248 | Enhance Policy Node with Auto-Fix Capabilities | HIGH | DONE |
| #249 | Align Organizational and Governance Nodes (Component, Label) | MEDIUM | DONE |
| #250 | Align Intelligence Pillar (User, Agent, Reasoning, Embedding) | HIGH | DONE |
| #251 | Align Code-as-Graph Pillar Entities (File, Symbol, Import) | HIGH | DONE |
| #252 | Implement Commit Node and Traceability Relationships | HIGH | DONE |
| #253 | Comprehensive Neo4j Repository Refactor for v1.0 Alignment | CRITICAL | DONE |
| #254 | Implement Relationship-Level Properties and Global Enums | MEDIUM | DONE |
| #255 | Implement Database Constraints and Vector Search Indexing | HIGH | DONE |
| #256 | Recursive and Domain-Driven Specialty Relationships | MEDIUM | DONE |
| #257 | Align Issue Node and Cross-Pillar Relationships | HIGH | DONE |
| #258 | Advanced AI Context & RAG Pre-filtering | MEDIUM | DONE |
| #259 | Automated Integrity and Self-Healing Logic | HIGH | DONE |

---

### Phase 4: High-Level Autonomy
- [x] Bidirectional Linkage (Issue-Code)
- [x] Phantom Dependency Detection (RAG-powered)
- [x] Autonomous Architect Agent
- [x] Pre-emptive Impact Analysis
- [x] Self-Healing Documentation
- [x] Autonomous Agent Workload Dispatcher
- [x] Reasoning Visualization in Vue Dashboard
- [x] Project Node Hierarchy
- [x] RAG Embedding Storage Optimization
- [x] Dynamic Internal Imports
- [x] Code Graph Stale Node Pruning
- [x] Agent Heartbeat Mechanism
- [x] RAG Context Window Manager

### Phase 5: v1.0 Data Model Alignment
- [x] Implement Project Entity in Core Domain (#246)
- [x] Align Neo4j Project Schema with v1.0 Documentation (#247)
- [x] Enhance Policy Node with Auto-Fix Capabilities (#248)
- [x] Align Organizational and Governance Nodes (Component, Label) (#249)
- [x] Align Intelligence Pillar (User, Agent, Reasoning, Embedding) (#250)
- [x] Align Code-as-Graph Pillar Entities (File, Symbol, Import) (#251)
- [x] Implement Commit Node and Traceability Relationships (#252)
- [x] Comprehensive Neo4j Repository Refactor for v1.0 Alignment (#253)
- [x] Relationship-Level Properties and Enums (#254)
- [x] Database Constraints and Vector Indexing (#255)
- [x] Recursive and Specialty Relationships (#256)
- [x] Issue Node and Cross-Pillar Alignment (#257)
- [x] Advanced AI Context & RAG Logic (#258)
- [x] Integrity and Self-Healing Guards (#259)
