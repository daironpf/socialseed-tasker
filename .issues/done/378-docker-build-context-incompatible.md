# Issue #378: Docker build context incompatible with fresh projects

## Description
When running `tasker init` in API mode, the Docker build fails because the Dockerfile (`.agent/tasker/Dockerfile`) expects `pyproject.toml` and `src/` in the build context (`.agent/`), but these files don't exist in a freshly scaffolded project. The Dockerfile assumes the project has its own source code, which breaks the out-of-the-box experience for new users.

## Expected Behavior
`tasker init` with API mode should successfully build and start all Docker containers without requiring manual file copies.

## Actual Behavior
Docker build fails with: `failed to calculate checksum of ref ... "/src": not found"` and `"/pyproject.toml": not found`. The command exits with a non-zero status and the API container is not started.

## Steps to Reproduce
1. `tasker install .` in an empty directory
2. `tasker init` selecting API mode (option 2)
3. Docker build fails during `docker compose --profile api up -d --build`

## Status: PENDING

## Priority: HIGH

## Component
Docker, Scaffold, tasker init

## Suggested Fix
Either:
- Make Dockerfile build optional and use a pre-built registry image by default
- Scaffold a minimal `pyproject.toml` in the build context directory
- Fall back to Direct mode gracefully if Docker build fails
- Add the parent project's source files to the build context

## Impact
Prevents API mode from working out-of-the-box for new projects. Users must manually copy files or use Direct mode.

## Related Issues
- (none)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
