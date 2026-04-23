# Issue #58: Fix stale Docker image - API shows v0.1.0 instead of v0.5.0

## Description

The Docker Compose container for `tasker-api` runs a cached image that reports version `0.1.0` in the `/health` endpoint, while the actual codebase is at `v0.5.0`. This causes confusion when verifying the deployed version and means the published Docker image on any registry is outdated.

## Problem Found

During the ecommerce setup test, `curl http://localhost:8000/health` returned `{"status":"healthy","version":"0.1.0"}` even though `pyproject.toml` and all source files were updated to `0.5.0`. The image had to be rebuilt manually with `docker compose build tasker-api`.

## Impact

- Users cannot verify which version is running
- PyPI package is v0.5.0 but Docker image is v0.1.0 - inconsistency
- CI/CD release workflow should rebuild and push the Docker image automatically

## Suggested Fix

- Add Docker image push step to `.github/workflows/release.yml`
- Tag Docker images with version: `socialseed-tasker:0.5.0` and `socialseed-tasker:latest`
- Add `docker compose pull` fallback in README if local build fails

## Priority

HIGH

## Labels

docker, release, ci-cd
