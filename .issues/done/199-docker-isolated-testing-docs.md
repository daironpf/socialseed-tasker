# Issue #199 - Docker Compose Isolated Testing Documentation

## Description

The `docker-compose.yml` references the `frontend/` directory for building, but in an isolated test environment (e.g., `real-test/`), the frontend directory must be manually copied. The CLI `tasker init` creates a new scaffold but doesn't integrate with existing Docker builds.

## Problem

When running `docker-compose build` in an isolated test directory:
1. `docker-compose.yml` expects `frontend/` directory with Dockerfile
2. `frontend/Dockerfile` expects `frontend/package.json`, `frontend/dist/`, `frontend/nginx.conf`
3. Build fails with `/frontend/package.json: not found`

## Status: COMPLETED

## Priority

**HIGH** - Blocks isolated testing

## Component

Docker, Documentation, CLI

## Changes Made

### 1. Created `docker-compose-minimal.yml` (root directory)

A new compose file with only Neo4j for isolated testing:
- Neo4j container with health check
- No API or frontend services
- Ideal for CLI testing and API development

```bash
# Usage
docker compose -f docker-compose-minimal.yml up -d
```

### 2. Created `docker-compose-minimal.yml` (templates)

Added to the scaffolder templates so `tasker init` includes it:
- `src/socialseed_tasker/assets/templates/docker-compose-minimal.yml`

### 3. Updated README.md

Added comprehensive "Isolated Testing" section:
- Quick start for API + Neo4j only
- Full stack isolated testing instructions
- Table of required files for full stack

### 4. Added Docker Troubleshooting Section

New troubleshooting guide in README covering:
- `/frontend/package.json: not found` - Solution provided
- `host not found in upstream "tasker-api"` - Solution provided
- Neo4j container not healthy - Reset instructions
- Port already in use - How to find and resolve
- `tasker` command not found - PATH solutions

## Verification

### Ruff Check
```bash
$ python -m ruff check src/
All checks passed!
```

### Tests
```bash
$ python -m pytest tests/unit/ -q
454 passed, 1 skipped, 1 warning in 26.87s
```

## Impact

Junior Dev users now have clear paths for isolated testing:
- API + Neo4j only: Use `docker-compose-minimal.yml`
- Full stack: Follow comprehensive setup guide
- Troubleshooting: Common issues documented with solutions

## Related Issues

- Issue #167: tasker init incomplete docker-compose (related)
- Issue #168: Missing Documentation in Scaffold (related)
- Real-Test Evaluation: FIND-001