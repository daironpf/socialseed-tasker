# Issue #357: docker-compose.yml dockerfile path breaks in Docker Compose v2

## Description
The docker-compose.yml specifies `dockerfile: .agent/tasker/Dockerfile` with `context: ../../..`. In Docker Compose v2, the `dockerfile` path is resolved relative to the project directory (where docker-compose.yml is) rather than the build context, causing build failures with "/src: not found".

## Expected Behavior
`docker compose build tasker-api` should succeed.

## Actual Behavior
Build fails with: `failed to compute cache key: failed to calculate checksum of ref ... "/src": not found`.

## Steps to Reproduce
1. Run `tasker install .`
2. Run `docker compose build tasker-api` from `.agent/tasker/`
3. Build fails

## Status: PENDING

## Priority: MEDIUM

## Component
Docker

## Suggested Fix
Either make the dockerfile path absolute relative to the context, or restructure the compose file to avoid the context/dockerfile path mismatch. Direct `docker build -f .agent/tasker/Dockerfile -t tasker-api .` works.

## Impact
CI/CD pipelines using docker-compose fail to build the API image.
