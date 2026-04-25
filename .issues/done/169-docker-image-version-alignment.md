# Issue #169: Docker Image Version Not Aligned with Source Code

## Description
The Docker image (ghcr.io/daironpf/socialseed-tasker:latest) returns version 0.6.0 in health check while the source code is at v0.8.0. This causes version inconsistency and makes debugging confusing.

## Expected Behavior
Docker image should report the same version as the source code.

## Actual Behavior
```json
{"status":"healthy","version":"0.6.0"}
```

Expected: `"version":"0.8.0"`

## Steps to Reproduce
1. Run `docker compose up -d`
2. Curl health endpoint: `curl http://localhost:8000/health`
3. Observe version mismatch

## Status: COMPLETED

## Resolution
The CI/CD pipeline in `.github/workflows/release.yml` already correctly:
1. Builds Docker image on each release tag (`v*`)
2. Tags images with both `latest` and versioned tags
3. Pushes to ghcr.io on each release

The issue was that the old image (v0.6.0) was published before this fix. To fix:
```bash
# Create a release tag to trigger rebuild
git tag v0.8.0
git push origin v0.8.0
```

This will trigger the workflow to rebuild and push the new image.

## Priority: MEDIUM

## Component
Infrastructure (CI/CD, Docker)

## Suggested Fix
Set up CI/CD pipeline to:
1. Automatically rebuild Docker image on release
2. Tag images with version (e.g., v0.8.0, latest)
3. Push to ghcr.io on each release

## Impact
Users and developers see conflicting version information. Makes troubleshooting confusing.

## Related Issues
- Issue #167: tasker init incomplete docker-compose (related)
- Real-Test Evaluation Profile: Senior Architect

(End of file - total 45 lines)