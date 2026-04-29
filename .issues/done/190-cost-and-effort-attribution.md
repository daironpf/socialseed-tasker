# Issue #190 - Cost and Effort Attribution

## Description

Add time tracking and cost estimation to Issues, enabling Capitalized Software Development tracking for enterprise accounting.

## Problem

Enterprise users (especially Fortune 100) need to track development costs per component for accounting purposes. Current system has no notion of effort estimation.

## Acceptance Criteria

- [x] Add fields to Issue entity:
  - `estimated_hours: float | None`
  - `hourly_rate_tier: HourlyRateTier` (JUNIOR, SENIOR, STAFF, PRINCIPAL)
  - `actual_hours: float | None`
- [x] Add cost calculation to component: `GET /analytics/cost-per-component`
- [x] Add cost calculation to Epic: `GET /analytics/cost-per-epic`
- [x] Add cost calculation to Project: `GET /analytics/cost-per-project`
- [x] Update Issue creation API to accept time fields

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
| `/api/v1/cost-per-component` | GET | Component cost breakdown |
| `/api/v1/cost-per-epic` | GET | Epic cost breakdown |
| `/api/v1/cost-per-project` | GET | Project cost breakdown |
| `/api/v1/cost-summary` | GET | Overall cost summary |

## Business Value

- Track "Capitalized Software Development"
- ROI calculations per component
- Budget vs actual reporting

## Status

**COMPLETED** - April 26, 2026

### Implementation Summary

- Added time tracking fields to Issue entity (already present)
- Added HourlyRateTier enum with rate constants in value_objects.py:
  - JUNIOR: $75/hour
  - SENIOR: $125/hour  
  - STAFF: $175/hour
  - PRINCIPAL: $250/hour
- Added calculate_cost helper function
- Added Neo4j queries for cost breakdown by component, epic, project, and summary
- Added repository methods: get_cost_per_component, get_cost_per_epic, get_cost_per_project, get_cost_summary
- Added REST API endpoints for cost analytics

**Commit**: 44834ae