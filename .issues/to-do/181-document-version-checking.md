# Issue #181 - Document Version Checking Instructions

## Description

Users have no clear instructions on how to verify which version of SocialSeed Tasker they're running, especially when using Docker alongside pip installation.

## Problem

```bash
$ pip install socialseed-tasker
$ tasker init .
$ docker compose up -d
$ # Now which version am I running?
$ curl http://localhost:8000/health | jq .version
# Version from Docker container, not from pip
```

Users cannot easily determine:
1. Which pip package version is installed
2. Which Docker image version is running
3. Whether they match

## Root Cause

The documentation does not include clear version checking instructions.

## Expected Behavior

README.md should include a clear "Checking Your Version" section:

```bash
# Check pip package version
pip show socialseed-tasker | grep Version

# Check Docker container version
curl http://localhost:8000/health | jq .version

# Verify CLI version
tasker --version  # After #180 is implemented
```

## Implementation Steps

### Step 1: Add version checking section to README.md

Add a new section after "Quick Start":

```markdown
## Checking Your Version

### PyPI Package Version
```bash
pip show socialseed-tasker
```

### Docker Container Version
```bash
curl http://localhost:8000/health | jq .version
```

### CLI Version
```bash
tasker --version
```

> **Note**: The Docker and CLI versions should match for consistent behavior.
```

### Step 2: Verify the documentation is clear

Ensure users understand:
- `latest` Docker tag always matches the latest release
- PyPI and Docker versions are released together

## Affected Files

- `README.md`

## Verification

Users should be able to find version checking instructions easily.

## Status: PENDING