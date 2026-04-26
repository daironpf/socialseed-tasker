# Issue #191 - Deployment and Environment Traceability

## Description

Track which Issues are deployed to which environments (Prod, Staging, Dev), enabling full deployment traceability from code to production.

## Problem

No way to know what Issue is deployed where. Enterprise needs to trace deployments for compliance and incident response.

## Acceptance Criteria

- [ ] Add new entities: `Environment` and `Deployment`
- [ ] Relationships:
  - `(Issue)-[:RELEASED_IN]->(Deployment)`
  - `(Deployment)-[:TO]->(Environment)`
- [ ] Environment types: PROD, STAGING, DEV, QA
- [ ] Webhook to receive CI/CD events: `POST /api/v1/deployments`
- [ ] Link Issues to Deployment via commit SHA
- [ ] Query: `GET /deployments?environment=PROD`
- [ ] Query: `GET /issues/{id}/deployments`

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
| `/api/v1/environments` | POST | Create Environment |
| `/api/v1/environments` | GET | List Environments |
| `/api/v1/deployments` | POST | Receive CI/CD webhook |
| `/api/v1/deployments` | GET | List Deployments |
| `/api/v1/deployments?env=PROD` | GET | Prod deployments |

## Business Value

- Deployment traceability for compliance
- Incident response: "What changed in PROD?"
- Audit trails for regulators