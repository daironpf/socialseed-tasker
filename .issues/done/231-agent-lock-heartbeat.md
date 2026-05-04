---
title: "Agent Lease & Heartbeat Mechanism"
component: "Agent Lifecycle"
priority: "HIGH"
status: "DONE"
version: "v1.0.0"
---

# Issue #231: Agent Lease & Heartbeat Mechanism

## Description
Add lease-based locking with heartbeat to prevent stale locks.

## Acceptance Criteria
- [x] Add locked_until property to Issue entity.
- [x] Implement /api/v1/issues/{id}/agent/heartbeat endpoint.
- [x] Add query to release expired locks.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add locked_until field to Issue entity
- [x] Add POST /issues/{id}/agent/heartbeat endpoint
- [x] Add RELEASE_EXPIRED_LOCKS query

### Files Changed
- `entities.py`: Added locked_until field
- `routes.py`: Added heartbeat endpoint
- `queries.py`: Added lock queries

### Usage
```bash
# Agent renews lock
curl -X POST "http://localhost:8000/api/v1/issues/{id}/agent/heartbeat"
```
