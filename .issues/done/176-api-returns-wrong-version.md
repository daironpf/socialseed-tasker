# Issue #176 - API Returns Wrong Version in Docker Container

## Description

API health check returns version **0.6.0** instead of **0.8.0**. This mismatch indicates the running container has stale code from an older version.

## Expected Behavior

```
Command: curl http://localhost:8000/health
Response: {"status":"healthy","version":"0.8.0"}
```

## Actual Behavior

```
Command: curl http://localhost:8000/health
Response: {"status":"healthy","version":"0.6.0"}
```

## Steps to Reproduce

1. Start services with `docker compose up -d`
2. Run `curl http://localhost:8000/health`
3. Observe version is 0.6.0 instead of 0.8.0

## Root Cause

The `ghcr.io/daironpf/socialseed-tasker:latest` Docker image is only rebuilt when a **new git tag** is pushed. The last tag was `v0.6.0`, so the image still contains that version.

Current code has `__version__ = "0.8.0"` but no tag exists for it.

## Affected Files

- `Dockerfile` (root) - correct, just needs rebuild
- `.github/workflows/release.yml` - rebuilds on tag push (correct behavior)

## Suggested Fix

Create tag `v0.8.0` to trigger GitHub Actions workflow:

```bash
git tag v0.8.0
git push origin v0.8.0
```

This will:
1. Trigger the `release.yml` workflow on the `v*` tag pattern
2. Build and push Docker image with v0.8.0 code
3. Publish to PyPI

## Impact

Agents relying on version check will assume old functionality is available, leading to unexpected behavior when using features added in v0.8.0.

## Resolution

Tag `v0.8.0` created and pushed. GitHub Actions will build and deploy the new Docker image.

## Status: COMPLETED