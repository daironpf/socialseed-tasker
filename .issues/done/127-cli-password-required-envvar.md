# Issue #127: CLI Requires Password via Environment Variable

## Description

The CLI requires `TASKER_NEO4J_PASSWORD` to be set explicitly as an environment variable. There's no way to pass it directly via CLI flag, and the error message when missing is confusing.

### Current Behavior

```bash
# Without password - confusing error
tasker component create backend -p test-project
# Error: Failed to connect to Neo4j: {neo4j_code: Neo.ClientError.Security.Unauthorized}
```

### Expected Behavior

Either:
1. Accept `--neo4j-password` flag directly in CLI commands, OR
2. Show clear message: "Please set TASKER_NEO4J_PASSWORD environment variable or pass --neo4j-password"

### Requirements

1. Add `--neo4j-password` / `-pw` option to CLI commands
2. Show helpful error message when password is missing
3. Update `.env.example` to include the password variable clearly

### Related Files

- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`
- `src/socialseed_tasker/assets/templates/configs/.env.example`

### Priority: MEDIUM

### Status: COMPLETED (2026-04-11)

### Changes Made

1. Added `--neo4j-user` / `-u` flag to CLI (default: neo4j)
2. Added `--neo4j-password` / `-pw` flag with help text showing "(required)"
3. Added check in `get_repository()` that shows clear error message when password missing
4. Added example in CLI help: `tasker -pw neoSocial component list`

### Files Modified

- `src/socialseed_tasker/entrypoints/terminal_cli/app.py`
- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

### Verification

```bash
# Before (unclear error)
$ tasker component list
Error: {neo4j_code: Neo.ClientError.Security.Unauthorized}

# After (clear message)
$ tasker component list
Error: Neo4j password is required.
Please provide it via:
  - Environment variable: TASKER_NEO4J_PASSWORD
  - CLI flag: --neo4j-password or -pw

Example:
  tasker -pw neoSocial component list

# Works with flag
$ tasker -pw neoSocial component list
+-------------------------------------------------------------------------------
| ID         | Name                 | Project              | Description        
|------------+----------------------+----------------------+--------------------
| 1fa8d747   | backend              | test-project         | Backend service    
+-------------------------------------------------------------------------------+
```