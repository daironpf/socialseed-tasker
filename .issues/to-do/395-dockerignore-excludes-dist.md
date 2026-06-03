# Issue #395: dist/ excluded by .dockerignore breaks docker compose build tasker-api

## Description
The `.dockerignore` file at the project root contains `dist`, which excludes the `dist/` directory from the Docker build context. Since the `Dockerfile` for `tasker-api` uses `COPY dist/ ./dist/` to install the wheel, `docker compose build tasker-api` fails with: `failed to compute cache key: "/dist": not found`.

## Expected Behavior
`docker compose --profile api build tasker-api` should succeed without additional manual steps.

## Actual Behavior
Build fails because `dist/` is excluded by `.dockerignore`. User must either remove `dist` from `.dockerignore`, copy the wheel elsewhere, or build with a separate Docker context.

## Steps to Reproduce
1. Run: `cd real-test && docker compose -f .agent/tasker/docker-compose.yml build tasker-api`
2. Observe: `ERROR: failed to compute cache key: "/dist": not found`

## Status: FIXED

## Priority: LOW

## Component
Docker

## Suggested Fix
Option A: Remove `dist` from `.dockerignore` and add a more specific ignore pattern instead.
Option B: Change the Dockerfile to build from the wheel published on PyPI instead of a local `dist/`.
Option C: Update the docker-compose.yml to use a different build context that includes `dist/`.

## Impact
Minor. Workaround exists: build wheel separately and use a temp directory or modify `.dockerignore` temporarily.

## Related Issues
- (none)

## Changes Made
Removed `dist` line from `.dockerignore` (line 2). This prevents Docker from excluding the `dist/` directory from the build context, allowing `COPY dist/ ./dist/` in the Dockerfile to succeed.

## Verification
`docker compose -f .agent/tasker/docker-compose.yml build tasker-api` should no longer fail with `cache key: "/dist": not found` when `dist/` exists.
