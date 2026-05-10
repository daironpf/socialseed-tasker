# Issue #272: Integrate Agent MUST_COMPLY_WITH Policy Validation

**Version:** 1.0.1
**Priority:** HIGH
**Status:** COMPLETED
**Assignee:** Agent

## Description
The graph model defines the relationship `(Agent)-[:MUST_COMPLY_WITH]->(Policy)` which mandates agents to check policy nodes during their reasoning process. This is now integrated into the agent workflow.

## Tasks
- [x] Add endpoint to validate code against policies: `POST /api/v1/policies/validate` (already existed)
- [x] Add endpoint to get policies for component: `GET /api/v1/policies/component/{component_id}`
- [x] Integrate policy validation into the close issue workflow
- [x] Handle BLOCKER severity - prevent closing if policy violated
- [x] Add force option to override policy violations

## Success Criteria
- [x] Agent can query policies for a component
- [x] Agent can validate changes against policies before closing
- [x] BLOCKER policies prevent issue closure
- [x] Force option available for override

## Graph Relationship
```
(Agent)-[:MUST_COMPLY_WITH]->(Policy)
(Project)-[:ENFORCES]->(Policy)
(Policy)-[:APPLIES_TO]->(Component)
```

## API Endpoints
```bash
# Get policies for component
GET /api/v1/policies/component/{component_id}

# Validate action against policies
POST /api/v1/policies/validate

# Close issue with policy validation
POST /api/v1/issues/{issue_id}/close?force=false

# Force close (override policy violations)
POST /api/v1/issues/{issue_id}/close?force=true
```

## Policy Severity Handling
- **BLOCKER (ERROR)**: Prevents issue closure unless ?force=true
- **WARNING**: Allowed (validation still runs)
- **INFO**: Just logged

## Related
- GraphDataModelDetails.md - Node: Policy (n13), Relationship: MUST_COMPLY_WITH
- Skill: programming-agent-governance.md - Policy Compliance section