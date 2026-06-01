# Issue #388: `tasker issue start` requires --agent-id but agent registration is broken

## Description
The `tasker issue start` command requires `--agent-id/-a` to mark an issue as in-progress. However, agent registration is broken (Issues #385 and #386), creating a circular dependency: you can't start work without an agent, and you can't register an agent.

## Expected Behavior
Either:
- Agent registration should work so `issue start` can be used, OR
- `issue start` should not require an agent-id for basic workflow, OR
- A default/dev agent should be auto-registered on first use

## Actual Behavior
```
$ tasker issue start c558c909
Error: Missing parameter: agent_id
```

## Steps to Reproduce
1. `tasker issue start <issue-id>`
2. Observe: Missing parameter error
3. Try to register an agent → fails (Issues #385, #386)

## Status: PENDING

## Priority: MEDIUM
