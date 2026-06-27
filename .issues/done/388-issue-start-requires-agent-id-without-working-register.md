# Issue #388: `tasker issue start` requires --agent-id but agent registration is broken

## Description
The `tasker issue start` command required `--agent-id/-a` as a mandatory parameter, but agent registration was broken (Issues #385 and #386), creating a circular dependency: you can't start work without an agent, and you can't register an agent.

## Root Cause
The `--agent-id` parameter was defined as required (`typer.Option(...)`) with no default. The `start_agent_work` and `finish_agent_work` repository methods only store the agent_id as a string marker on the Issue node — they don't validate against any registered agent list. So there's no technical reason to require a pre-registered agent ID.

## Fix
- Made `--agent-id` optional in both `issue start` and `issue finish` commands
- Default value: `"dev-agent"` — a sensible default for development workflows
- Users can still override with `--agent-id custom-agent` if they need to track specific agents

## Files Changed
- `src/socialseed_tasker/cli/commands/issue_commands.py:398` — `issue_start`: `...` → `"dev-agent"`
- `src/socialseed_tasker/cli/commands/issue_commands.py:430` — `issue_finish`: `...` → `"dev-agent"`

## Verification
- `tasker issue start --help` now shows: `--agent-id -a TEXT  Agent identifier (default: dev-agent) [default: dev-agent]`
- All 800 unit tests pass.

## Status: DONE
