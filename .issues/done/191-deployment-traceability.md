# Issue #191 - Deployment and Environment Traceability

## Description

Track which Issues are deployed to which environments (Prod, Staging, Dev), enabling full deployment traceability from code to production.

## Problem

No way to know what Issue is deployed where. Enterprise needs to trace deployments for compliance and incident response.

## Acceptance Criteria

- [x] Add new entities: `Environment` and `Deployment`
- [x] Relationships:
  - `(Issue)-[:RELEASED_IN]->(Deployment)`
  - `(Deployment)-[:TO]->(Environment)`
- [x] Environment types: PROD, STAGING, DEV, QA
- [x] Webhook to receive CI/CD events: `POST /api/v1/deployments`
- [x] Link Issues to Deployment via commit SHA
- [x] Query: `GET /deployments?environment=PROD`
- [x] Query: `GET /issues/{id}/deployments`

## Technical Notes

```python
class Environment(BaseModel):
    id: UUID
    name: str  # PROD, STAGING, DEV, QA
    url: str | None
    is_active: bool

class Deployment(BaseModel):
    id: UUID
    commit_sha: str
    environment_id: UUID
    deployed_at: datetime
    issue_ids: list[UUID]
    channel: str  # slack, email, webhook
```

Relationships:
```cypher
(issue:Issue)-[:RELEASED_IN]->(deployment:Deployment)-[:TO]->(env:Environment)
```

Webhook payload (CI/CD):
```json
{
  "commit_sha": "abc123",
  "environment": "PROD",
  "issue_ids": ["uuid1", "uuid2"],
  "deployed_by": "github-actions"
}
```

## API Impact

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/api/v1/deployments` | POST | Receive CI/CD webhook |
| `/api/v1/deployments` | GET | List Deployments |
| `/api/v1/deployments?env=PROD` | GET | Prod deployments |
| `/api/v1/deployments/by-commit/{sha}` | GET | Get by commit |
| `/api/v1/issues/{id}/deployments` | GET | Issue's deployments |

## Business Value

- Deployment traceability for compliance
- Incident response: "What changed in PROD?"
- Audit trails for regulators

## Status

**COMPLETED** - April 26, 2026

### Implementation Summary

- Added EnvironmentType enum (PROD, STAGING, DEV, QA) and Environment entity
- Added Deployment entity with commit_sha, environment_name, issue_ids
- Added Neo4j queries: CREATE_DEPLOYMENT, GET_DEPLOYMENTS, GET_DEPLOYMENT_BY_COMMIT, GET_ISSUES_DEPLOYMENTS
- Added repository methods for deployment operations
- Added REST API endpoints:
  - `POST /api/v1/deployments` - Receive CI/CD webhook
  - `GET /api/v1/deployments` - List deployments with environment filter
  - `GET /api/v1/deployments/by-commit/{sha}` - Get by commit SHA
  - `GET /api/v1/issues/{id}/deployments` - Get issue deployments

**Commit**: 28355b0