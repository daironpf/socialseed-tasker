# Issue #173: Frontend Not Connecting to API

## Description
The tasker-board frontend is running but not showing data from the API. The frontend cannot communicate with the API backend.

## Expected Behavior
- Board at http://localhost:8080 should display issues and components from API at http://localhost:8000

## Actual Behavior
- API: http://localhost:8000 works correctly
- Board: http://localhost:8080 loads but shows no data
- Console errors likely show CORS or network issues

## Steps to Reproduce
1. Run `docker compose up -d`
2. Open http://localhost:8080
3. Observe no issues/components displayed

## Status: PENDING

## Priority: HIGH

## Component
Frontend (tasker-board, Vue.js)

## Suggested Fix
Option A: Environment variable
```yaml
tasker-board:
  environment:
    - TASKER_API_URL=http://tasker-api:8000
```

Option B: CORS configuration in API
- Add CORS headers for frontend origin

Option C: Proxy configuration in frontend
- Configure Vite proxy to forward API requests

## Impact
Users cannot use the visual Kanban board.

## Related Issues
- Issue #172: tasker-board not active
- Real-Test Evaluation FIND-002

(End file - 50 lines)