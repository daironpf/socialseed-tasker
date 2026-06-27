# Issue #275: Missing CLI Server Command

## Description
Users must use `python -m socialseed_tasker.entrypoints.web_api` to start the API server. There is no documented CLI command like `tasker serve` or `tasker api` in the tasker help output.

## Expected Behavior
A simple CLI command like `tasker serve` or `tasker api` should start the API server.

## Actual Behavior
`tasker --help` does not show any server/start command. Users must know to use the Python module invocation.

## Steps to Reproduce
1. Run `tasker --help`
2. Observe no server/start command is available

## Status: COMPLETED

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Add a `tasker serve` or `tasker api` command to the CLI that starts the FastAPI server using uvicorn with proper configuration from environment variables.

## Impact
Increases setup friction for new users who don't know how to start the API server programmatically.

## Related Issues
- Related to issue #6 (Implement Typer CLI)