# Issue #207: Real-Test Scaffold Uses Pre-built Image Without Local Fixes

## Description

The real-test scaffold (`tasker init`) generates a docker-compose.yml that uses the pre-built Docker image from GitHub Container Registry (`ghcr.io/daironpf/socialseed-tasker:latest`). When testing local fixes, the evaluation must rebuild the image locally with `docker compose build tasker-api`, adding friction to the testing workflow.

## Problem

```yaml
# Generated docker-compose.yml uses:
tasker-api:
    image: ghcr.io/daironpf/socialseed-tasker:latest

# But local fixes are not in the pre-built image
# Must rebuild: docker compose build tasker-api
```

This increases testing time and complexity when evaluating local code changes.

## Expected Behavior

The scaffold should support local development mode where changes to `src/` are reflected without rebuilding, or clearly indicate that local builds are needed.

## Steps to Reproduce

```bash
tasker init .
# Edit src/ with fixes
docker compose up -d
# API doesn't have fixes (uses pre-built image)
# Must: docker compose build tasker-api
```

## Status

**TODO**

## Priority

**LOW** - Minor testing friction

## Component

DOCKER, WORKFLOW

## Acceptance Criteria

- [ ] Scaffold supports local development without rebuild
- [ ] OR: Documentation explains need for local build
- [ ] OR: Provide build command in scaffold output

## Suggested Fix

Option 1 (Volume mount):
```yaml
tasker-api:
    volumes:
      - ../../src/:/app/src/
```

Option 2 (Build by default):
```yaml
tasker-api:
    build:
      context: ../..
      dockerfile: Dockerfile
```

Option 3 (Documentation):
Add note in scaffold output about building for local testing.

## Impact

- Slower testing workflow
- Additional friction for developers testing local changes

## Related Issues

- Real-Test Evaluation workflow