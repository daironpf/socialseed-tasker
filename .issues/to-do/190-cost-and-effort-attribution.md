# Issue #190 - Cost and Effort Attribution

## Description

Add time tracking and cost estimation to Issues, enabling Capitalized Software Development tracking for enterprise accounting.

## Problem

Enterprise users (especially Fortune 100) need to track development costs per component for accounting purposes. Current system has no notion of effort estimation.

## Acceptance Criteria

- [ ] Add fields to Issue entity:
  - `estimated_hours: float | None`
  - `hourly_rate_tier: HourlyRateTier` (JUNIOR, SENIOR, STAFF, PRINCIPAL)
  - `actual_hours: float | None`
- [ ] Add cost calculation to component: `GET /analytics/cost-per-component`
- [ ] Add cost calculation to Epic: `GET /analytics/cost-per-epic`
- [ ] Add cost calculation to Project: `GET /analytics/cost-per-project`
- [ ] Update Issue creation API to accept time fields

## Technical Notes

```python
class HourlyRateTier(str, Enum):
    JUNIOR = "JUNIOR"  # $75/hour
    SENIOR = "SENIOR"  # $125/hour
    STAFF = "STAFF"    # $175/hour
    PRINCIPAL = "PRINCIPAL"  # $250/hour
```

Cost calculation (Cypher):
```cypher
MATCH (i:Issue)-[:BELONGS_TO]->(c:Component)
WHERE i.status = 'CLOSED'
WITH c, COLLECT(i.actual_hours * i.hourly_rate_tier) as costs
RETURN c.name, REDUCE(s = 0, x IN costs | s + x) as total_cost
```

## API Impact

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/api/v1/issues` | POST | Accept estimated_hours, hourly_rate_tier |
| `/api/v1/issues/{id}` | PATCH | Update hours |
| `/analytics/cost-per-component` | GET | Component cost breakdown |
| `/analytics/cost-per-epic` | GET | Epic cost breakdown |
| `/analytics/cost-per-project` | GET | Project cost breakdown |

## Business Value

- Track "Capitalized Software Development"
- ROI calculations per component
- Budget vs actual reporting