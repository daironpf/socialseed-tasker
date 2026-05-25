# Issue #328: Docker build fails with 403 Forbidden from ghcr.io

## Description
The scaffolded Dockerfile (`real-test/.agent/tasker/Dockerfile`) copies a binary from a GitHub Container Registry public image:

```dockerfile
COPY --from=ghcr.io/lexifuse/neo4j-mcp-server:latest /usr/local/bin/neo4j-mcp-server /usr/local/bin/
```

This fails with a 403 Forbidden error because anonymous pull requests to `ghcr.io` require authentication.

## Expected Behavior
`docker build -t tasker-api:local .` should succeed without authentication.

## Actual Behavior
```
failed to authorize: failed to fetch anonymous token:
unexpected status from GET request to ... : 403 Forbidden
```

## Steps to Reproduce
1. Run `tasker install .` to scaffold a project
2. Run `docker build -t tasker-api:local -f .agent/tasker/Dockerfile .`
3. Observe 403 Forbidden error

## Status: PENDING

## Priority: MEDIUM

## Component
DOCKER — `real-test/.agent/tasker/Dockerfile` (line 11)

## Suggested Fix
Option 1: Make the COPY conditional (already has `|| true` but fails before reaching it)
Option 2: Remove the `neo4j-mcp-server` binary from the Dockerfile
Option 3: Use a different image that allows anonymous pulls
Option 4: Add `docker login ghcr.io` documentation step

## Impact
- Users cannot build the Docker image for the API
- `docker compose up` fails on first run
- Workaround: Use local `pip install` instead of Docker for the API
