# Issue #225: Autonomous Agent Workload & Dispatcher

## Description
A central dispatcher that assigns issues to available agents based on their capabilities and current workload.

## Acceptance Criteria
- [x] Agent registry with `capabilities` and `status`.
- [x] Dispatcher logic to assign `OPEN` issues to `IDLE` agents.
- [x] Priority-based queuing.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add `tasker agent list` command
- [x] Add `tasker agent dispatch` command
- [x] Priority-based queuing (CRITICAL > HIGH > MEDIUM > LOW)
- [x] Sets agent_working flag on issues

### Files Changed
- `commands.py`: Added agent list and dispatch commands

### Usage
```bash
# List working agents
tasker agent list

# Dispatch top issues to agents
tasker agent dispatch --limit 5

# Output shows dispatched issues with priorities
```
