# Issue #117: Fix API Version Mismatch in Running Container

## Description

The health endpoint in the running Docker container returns version "0.5.0" but the project version is 0.8.0. This is because the Docker image was built from an older version.

## Current Behavior
```json
GET /health
{
  "status": "healthy",
  "version": "0.5.0"  // Wrong version
}
```

## Expected Behavior
```json
GET /health
{
  "status": "healthy",
  "version": "0.8.0"
}
```

## Root Cause

The Docker image (tasker-api) was built from a previous version. The code in `src/socialseed_tasker/__init__.py` correctly has `__version__ = "0.8.0"`, but the running container has old code.

## Requirements

- Rebuild the Docker image with latest code
- Or update the running container with new code
- Verify health endpoint shows correct version

## Status: COMPLETED