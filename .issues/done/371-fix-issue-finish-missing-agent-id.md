# Issue #371: issue finish missing --agent-id parameter

## Description
`tasker issue start` requires `--agent-id` to track which agent started work on an issue, but `tasker issue finish` does not accept `--agent-id`. This creates an inconsistency where work can be started by an agent but cannot be finished by the same agent, breaking the agent traceability lifecycle.

## Expected Behavior
`tasker issue finish` should accept an `--agent-id` parameter (matching `issue start`) to properly close the agent work cycle.

## Actual Behavior
```
$ tasker issue finish --help
Usage: tasker issue finish [OPTIONS] ISSUE_ID
Arguments:
  *    issue_id      TEXT  [required]
Options:
  --help          Show this message and exit.

No --agent-id option available.
```

## Steps to Reproduce
1. Run `tasker issue start <id> --agent-id "test-agent"`
2. Try `tasker issue finish <id> --agent-id "test-agent"`
3. Observe error: "No such option: --agent-id"

## Status: PENDING

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Add `--agent-id` parameter to `issue finish` command, mirroring the same parameter in `issue start`.

## Impact
Medium — breaks agent traceability in the work lifecycle.
