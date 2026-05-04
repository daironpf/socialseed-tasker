# Issue #225: Autonomous Agent Workload & Dispatcher

## Description
A central dispatcher that assigns issues to available agents based on their capabilities and current workload.

## Acceptance Criteria
- [ ] Agent registry with `capabilities` and `status`.
- [ ] Dispatcher logic to assign `OPEN` issues to `IDLE` agents.
- [ ] Priority-based queuing.

## Technical Notes
- Uses the `Agent` node properties in Neo4j.
- Dispatcher runs as a standalone service or CLI loop.
