# Issue #372: Docker API build fails in clean scaffold

## Description
When scaffolding Tasker into a new project with no source code, the Docker build for `tasker-api` fails because the Dockerfile expects `src/` and `pyproject.toml` in the build context. The docker-compose.yml build context (`context: ..` from `.agent/tasker/`) points to the project root, but in a fresh scaffold these files don't exist yet.

## Expected Behavior
The Docker build should succeed in a clean scaffold, or provide clear documentation on how to set up API mode for new projects.

## Actual Behavior
COPY commands in Dockerfile fail with errors:
```
COPY pyproject.toml README.md ./  → not found
COPY src/ ./src/                  → not found
```

## Steps to Reproduce
1. Create a new project directory
2. Run `tasker install .` then `tasker init` with API mode
3. Run `docker compose build tasker-api`
4. Observe build failure

## Status: PENDING

## Priority: MEDIUM

## Component
DOCKER

## Suggested Fix
Either: a) Document that API mode requires existing source code, b) provide a fallback default image from a registry, or c) make the Dockerfile conditional.

## Impact
Medium — blocks API mode setup for new projects.
