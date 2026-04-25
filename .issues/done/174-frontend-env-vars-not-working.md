# Issue #174: Frontend Environment Variables Not Working at Runtime

## Description
Despite adding VITE_API_URL and VITE_API_KEY environment variables to docker-compose, the pre-built frontend image doesn't connect to the API. The pre-built image may not support runtime environment variables.

## Expected Behavior
- Board at http://localhost:8080 should display issues from API at http://localhost:8000

## Actual Behavior
- Added docker-compose env vars:
  - VITE_API_URL=http://tasker-api:8000/api/v1
  - VITE_API_KEY=test-token
- Board still shows NO data

## Steps to Reproduce
1. Run `docker compose up -d`
2. Check board at http://localhost:8080
3. Observe no data displayed

## Status: COMPLETED

## Resolution
Used runtime configuration via window global variables:

1. Modified `frontend/src/api/client.ts`:
```typescript
const API_URL = (window as any).__API_URL__ || '/api/v1'
const API_KEY = (window as any).__API_KEY__ || ''
```

2. Added in `frontend/index.html`:
```html
<script>
  window.__API_URL__ = 'http://localhost:8000/api/v1';
  window.__API_KEY__ = 'test-token';
</script>
```

3. Build steps:
```bash
cd frontend && npm run build
docker build -t my-board:latest .
docker-compose up -d --force-recreate tasker-board
```

This works because the config is embedded in the HTML at build time.

## Priority: HIGH

## Component
Frontend (Docker, environment)

## Suggested Fix
Option A: Rebuild image with env vars at build time
- Build image locally: `docker build --build-arg VITE_API_URL=...`

Option B: Use nginx config to proxy requests
- Configure nginx to proxy /api to tasker-api

Option C: Build frontend dynamically
- Use docker-compose profiles or startup script

## Impact
Users cannot see their issues in the visual Kanban board.

## Related Issues
- Issue #173: Frontend not connecting (previous attempt)
- Issue #172: tasker-board

(End file - 45 lines)