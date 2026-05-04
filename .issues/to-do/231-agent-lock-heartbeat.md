---
title: "Agent Lease & Heartbeat Mechanism"
component: "Agent Lifecycle"
priority: "HIGH"
status: "TODO"
version: "v1.0.0"
---

# Issue #231: Agent Lease & Heartbeat Mechanism

## Description
The current system uses a simple boolean flag `agent_working` to prevent multiple agents from working on the same issue. If an agent crashes, gets disconnected, or hits a fatal error, the issue remains locked indefinitely (`agent_working=true`), requiring manual intervention to unlock it.

## Acceptance Criteria
- [ ] Replace or augment `agent_working` with a `locked_until` (DateTime) property.
- [ ] Implement an API endpoint `/api/v1/issues/{id}/heartbeat` that agents must call periodically (e.g., every 5 minutes) to renew their lock lease.
- [ ] Implement a background task or query logic that automatically treats issues with expired `locked_until` timestamps as unlocked.
- [ ] Add an `agent_crashed` or `lease_expired` status to the `ReasoningNode` or Issue timeline to explicitly record why an agent stopped working.

## Technical Notes
- The heartbeat interval should be configurable via an environment variable (`TASKER_AGENT_HEARTBEAT_INTERVAL`).
- This makes the framework much more resilient to unstable agent environments.
