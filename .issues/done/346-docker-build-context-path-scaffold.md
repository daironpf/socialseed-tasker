# Issue #346: Scaffolded docker-compose context path assumes project source at root

## Description
The generated `docker-compose.yml` sets `context: ../..` from `.agent/tasker/`. This works when the project source is in the parent directory, but not when the user initializes Tasker in a brand new project without source code (e.g., from a blank directory). The Docker build fails because `pyproject.toml` and `src/` don't exist at the expected path.

## Expected Behavior
The scaffolded docker-compose should work in a blank project directory, or provide a clear error message explaining the source code requirement.

## Actual Behavior
Docker build fails with:
```
failed to compute cache key: "/pyproject.toml": not found
```

## Steps to Reproduce
1. Create a new empty directory
2. Run `tasker install .` and `tasker init` (or manual setup)
3. Run `docker compose --profile api up -d --build`
4. Observe build failure

## Status: PENDING

## Priority: LOW

## Component
DOCKER

## Suggested Fix
Either publish the API image to a registry so it can be pulled directly, or add a fallback Dockerfile that doesn't require project source code, or provide clear setup documentation for the build context requirement.

## Impact
New users who scaffold Tasker in a fresh project cannot start the API without creating dummy source files.

## Related Issues
- FIND-005 from black-box evaluation 2026-05-28
