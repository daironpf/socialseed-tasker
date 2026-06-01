# Issue #385: `tasker agent register` uses wrong default API port (:8000 vs :8888)

## Description
The `agent register` CLI command hardcodes `os.getenv("TASKER_API_URL", "http://localhost:8000")` with default port 8000, while the rest of the CLI correctly reads `api_url: http://localhost:8888` from `.agent/configs/tasker.yml` via DualModeConfig. This causes a misleading "Cannot connect to API" error.

## Expected Behavior
`tasker agent register` should use the same API URL resolution as the rest of the CLI (DualModeConfig), defaulting to the configured port (8888) instead of 8000.

## Actual Behavior
```
$ tasker agent register -i dev-agent-01 -n "Developer Agent"
Cannot connect to API. Is the server running?
```
Works only after manually setting `$env:TASKER_API_URL="http://localhost:8888"`.

## Steps to Reproduce
1. Configure tasker with `mode: api` and `api_url: http://localhost:8888`
2. Run `tasker agent register -i test -n "Test" -r developer`
3. Observe: "Cannot connect to API. Is the server running?"

## Root Cause
`src/socialseed_tasker/cli/commands/agent_commands.py:175` uses a hardcoded default instead of reading from the DualModeConfig that the rest of the CLI uses.

## Status: PENDING

## Priority: MEDIUM
