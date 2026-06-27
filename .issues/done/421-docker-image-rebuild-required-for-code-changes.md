# Issue #421: Docker image rebuild required for source code changes to take effect

## Description
Running the API via Docker (`tasker init`) builds a Docker image (`tasker-api:local`) that packages the source code at build time. Subsequent source code changes (e.g., fixing the reasoning endpoint response format) are not reflected in the running API container until `tasker init` is run again to rebuild the image.

This creates a poor developer experience where code changes are not immediately testable in the Docker environment.

## Expected Behavior
Either the Docker image should be rebuilt automatically when changes are detected, or the API should be runnable in development mode that mounts the source code directory as a volume.

## Actual Behavior
Source code changes are ignored by the running Docker container. Only `tasker init` (which rebuilds the image) or manual `docker compose build tasker-api` makes them effective.

## Steps to Reproduce
1. Make a change to `src/socialseed_tasker/infrastructure/web_api/routers/issues.py`
2. Run `docker compose restart tasker-api`
3. Observe the change is NOT reflected (old behavior persists)
4. Run `tasker init` to rebuild the image — change is now visible

## Status: RESOLVED

## Priority: LOW

## Component
DOCKER

## Suggested Fix
Add a development docker-compose profile that mounts `src/` as a volume, enabling hot-reload with `uvicorn --reload`. Or add a `tasker dev` command that handles this automatically.

## Impact
Low. Workaround exists (run `tasker init` or `docker compose build`). Only affects developers making source-level changes while testing via Docker.

## Related Issues
- (none)

## Changes Made
1. Created `docker-compose.dev.yml` at project root — a Docker Compose override that mounts `./src:/app/src` and `./pyproject.toml:/app/pyproject.toml`, sets `TASKER_DEBUG=true` (enables uvicorn `--reload`), and reinstalls the package in editable mode on startup.
2. Added `dev-api` target to `Makefile` — runs `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` for a one-command dev experience.
3. Updated `.agent/VERSIONS.md` and `.agent/ROADMAP.md`.

## Verification
1. Run `make dev-api` (or `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`).
2. Make a change to any source file (e.g., `src/socialseed_tasker/infrastructure/web_api/routers/issues.py`).
3. Observe that the API container auto-reloads (uvicorn logs will show "Reloading...").
4. The change is immediately reflected without rebuilding the Docker image.
