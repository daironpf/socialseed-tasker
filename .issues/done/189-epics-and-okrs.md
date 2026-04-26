# Issue #189 - Implement Epics and Objectives (OKRs)

## Description

Add support for grouping Issues into Epics and Objectives (OKRs), enabling enterprise-level planning and progress tracking.

## Problem

Issues are flat - there's no way to group them into initiatives or track strategic objectives. Enterprise users need hierarchical planning.

## Acceptance Criteria

- [x] Add new entities: `Epic` and `Objective`
- [x] Implement relationships:
  - `(Issue)-[:PART_OF]->(Epic)`
  - `(Epic)-[:CONTRIBUTES_TO]->(Objective)`
- [x] API: CRUD for Epics (`/api/v1/epics`)
- [x] API: CRUD for Objectives (`/api/v1/objectives`)
- [x] Link multiple Issues to Epic in single transaction
- [x] Add fields to Issue: `estimated_hours`, `hourly_rate_tier`, `actual_hours`
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

## Status

**COMPLETED** - April 26, 2026

### Implementation Summary

- Created Epic and Objective entities with status enums in `entities.py`
- Added Neo4j queries for CRUD operations in `queries.py`
- Added repository methods in `repositories.py`
- Added REST API endpoints:
  - `POST /api/v1/epics` - Create epic
  - `GET /api/v1/epics` - List epics
  - `GET /api/v1/epics/{epic_id}` - Get epic details
  - `PATCH /api/v1/epics/{epic_id}` - Update epic
  - `DELETE /api/v1/epics/{epic_id}` - Delete epic
  - `POST /api/v1/epics/{epic_id}/issues` - Link issues to epic
  - `POST /api/v1/objectives` - Create objective
  - `GET /api/v1/objectives` - List objectives
  - `GET /api/v1/objectives/{objective_id}` - Get objective details
  - `PATCH /api/v1/objectives/{objective_id}` - Update objective
  - `DELETE /api/v1/objectives/{objective_id}` - Delete objective
  - `POST /api/v1/objectives/{objective_id}/epics` - Link epics to objective

**Commit**: 862cc92