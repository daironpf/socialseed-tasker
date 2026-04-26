# Issue #189 - Implement Epics and Objectives (OKRs)

## Description

Add support for grouping Issues into Epics and Objectives (OKRs), enabling enterprise-level planning and progress tracking.

## Problem

Issues are flat - there's no way to group them into initiatives or track strategic objectives. Enterprise users need hierarchical planning.

## Acceptance Criteria

- [ ] Add new entities: `Epic` and `Objective`
- [ ] Implement relationships:
  - `(Issue)-[:PART_OF]->(Epic)`
  - `(Epic)-[:CONTRIBUTES_TO]->(Objective)`
- [ ] API: CRUD for Epics (`/api/v1/epics`)
- [ ] API: CRUD for Objectives (`/api/v1/objectives`)
- [ ] Link multiple Issues to Epic in single transaction
- [ ] Add fields to Issue: `estimated_hours`, `hourly_rate_tier`, `actual_hours`
- [ ] Add progress calculation on Epic (closed issues / total issues)
- [ ] Add progress calculation on Objective (sum of child Epics)

## Technical Notes

Entities:
```python
class Epic(BaseModel):
    id: UUID
    name: str
    description: str | None
    objective_id: UUID | None
    status: EpicStatus  # OPEN, IN_PROGRESS, COMPLETED
    issue_ids: list[UUID]

class Objective(BaseModel):
    id: UUID
    name: str
    description: str | None
    status: ObjectiveStatus  # OPEN, IN_PROGRESS, COMPLETED
    quarter: str  # e.g., "Q1-2026"
```

Relationships:
```cypher
(issue:Issue)-[:PART_OF]->(epic:Epic)-[:CONTRIBUTES_TO]->(objective:Objective)
```

## API Impact

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/api/v1/epics` | POST | Create Epic |
| `/api/v1/epics` | GET | List Epics |
| `/api/v1/epics/{id}` | GET | Get Epic with issues |
| `/api/v1/epics/{id}/issues` | POST | Link issues to Epic |
| `/api/v1/objectives` | POST | Create Objective |
| `/api/v1/objectives` | GET | List Objectives |
| `/api/v1/objectives/{id}/progress` | GET | Objective progress |

## Business Value

- Quarterly OKR tracking
- Epic-level progress for stakeholders
- Capitalized Software Development tracking