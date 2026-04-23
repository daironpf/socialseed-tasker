# Issue #01: CLI Authentication UX Improvement

## Description
The CLI requires the Neo4j password for every command if not set as an environment variable, making it tedious for manual use. Users need to repeatedly enter credentials.

## Expected Behavior
Implement a way to persist session or configuration (e.g., `tasker login` command or saving to a local config file after the first successful connection).

## Actual Behavior
Users must provide Neo4j password via environment variable or CLI flag for every command execution.

## Steps to Reproduce
1. Ensure TASKER_NEO4J_PASSWORD is not set as environment variable
2. Run any tasker CLI command (e.g., `tasker component list`)
3. Observe that password is required

## Status: PENDING

## Priority: MEDIUM

## Recommendations
- Implement `tasker login` command to securely store credentials
- Use local config file (e.g., `~/.tasker/config`) to persist authentication
- Support both environment variables and persistent storage
- Ensure secure credential storage (consider encryption)