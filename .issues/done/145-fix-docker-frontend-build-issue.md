# Fix Docker frontend build issue

**Status**: COMPLETED
**Priority**: MEDIUM
**Labels**: docker, build
**Created**: 2026-04-12

## Problem

The Docker build for the frontend (`tasker-board`) fails due to network connectivity issues during `npm ci`.

## Error

```
npm error code ECONNRESET
npm error network aborted
npm error network This is a problem related to network connectivity.
```

## Location

`frontend/Dockerfile:12`

## Current Behavior

The build fails during:
```dockerfile
RUN npm ci
```

## Expected Behavior

The frontend container should build successfully.

## Possible Solutions

### 1. Use npm install instead of npm ci
`npm install` is more resilient to network issues than `npm ci`:

```dockerfile
RUN npm install --prefer-offline || npm install
```

### 2. Add retry logic
Add retry mechanism for network operations:

```dockerfile
RUN for i in 1 2 3; do npm ci && break || echo "Retry $i"; done
```

### 3. Use npm cache
Enable Docker layer caching for npm:

```dockerfile
RUN --mount=type=cache,target=/root/.npm \
    npm ci
```

### 4. Offline mode
Check if npm packages can be pre-bundled:

```dockerfile
COPY package-lock.json ./
RUN npm ci --offline 2>/dev/null || npm install
```

## Test Commands

```bash
docker compose build tasker-board
docker compose up -d tasker-board
```

## Expected Result

Frontend container builds and runs successfully.

## Status: PENDING