# Issue #179 - Docker Image Version Mismatch with PyPI Package

## Description

The scaffolded `docker-compose.yml` references `ghcr.io/daironpf/socialseed-tasker:latest` which does not match the version of the installed PyPI package. Users running Docker and pip install may have different versions.

## Problem

When a user installs the package from PyPI:
```bash
pip install socialseed-tasker  # Installs 0.8.1
tasker init .                  # Scaffolds docker-compose.yml
cd tasker && docker compose up  # Uses ghcr.io/daironpf/socialseed-tasker:latest
```

The Docker image might be an older version (0.8.0) while the PyPI package is newer (0.8.1).

## Root Cause

The GitHub Actions workflow builds Docker image and PyPI package from the same tag, but:
1. The docker-compose template uses `latest` tag instead of versioned tags
2. There's no mechanism to ensure Docker and PyPI are built from the same commit
3. The `latest` tag is only updated when explicitly pushed

## Current docker-compose.yml template

```yaml
tasker-api:
  image: ghcr.io/daironpf/socialseed-tasker:latest
```

## Proposed Solution

Option 1: Use versioned tags in docker-compose template
```yaml
tasker-api:
  image: ghcr.io/daironpf/socialseed-tasker:0.8.1
```

Option 2: Build from source during scaffold (requires Docker build context)

Option 3: Update GitHub Actions to always push `latest` tag when a version tag is pushed

## Affected Files

- `src/socialseed_tasker/assets/templates/docker-compose.yml`

## Implementation Steps

### Step 1: Update release workflow
Update `.github/workflows/release.yml` to always push the `latest` tag:
```yaml
- name: Push Docker images
  run: |
    docker push ghcr.io/daironpf/socialseed-tasker:${{ github.ref_name }}
    docker push ghcr.io/daironpf/socialseed-tasker:latest  # Always update latest
```

### Step 2: Verify workflow execution
Ensure the workflow runs successfully for each version tag.

### Step 3: Document the behavior
Update README to clarify that `latest` Docker tag matches the latest PyPI version.

## Verification

```bash
# Check PyPI version
pip show socialseed-tasker | grep Version

# Check Docker image version
docker run --rm ghcr.io/daironpf/socialseed-tasker:latest --version 2>/dev/null || \
  curl -s http://localhost:8000/health | jq .version

# They should match
```

## Impact

Users will have consistent versions between pip install and Docker.

## Status: COMPLETED

## Implementation

The release workflow (`.github/workflows/release.yml`) already pushes both versioned and `latest` tags:

```yaml
tags: |
  ghcr.io/${{ github.repository_owner }}/socialseed-tasker:latest
  ghcr.io/${{ github.repository_owner }}/socialseed-tasker:${{ steps.version.outputs.VERSION }}
```

Added documentation comment in `docker-compose.yml` template to clarify:
```
# Note: 'latest' tag is always updated with each release to match PyPI version
```