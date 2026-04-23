# Issue #06: Frontend Authentication Handling

## Description
When `TASKER_AUTH_ENABLED=true` is set on the backend, the Vue dashboard breaks with `401 Unauthorized`. The frontend needs a login screen or an environment variable setup for `X-API-Key`.

## Expected Behavior
The Vue dashboard should either:
1. Include a login screen to authenticate with the backend API
2. Read the `X-API-Key` from an environment variable automatically
3. Gracefully handle 401 responses with a retry mechanism

## Actual Behavior
The frontend makes API calls without authentication when `TASKER_AUTH_ENABLED=true`, resulting in 401 Unauthorized errors and a broken dashboard.

## Steps to Reproduce
1. Set `TASKER_AUTH_ENABLED=true` on backend
2. Start the Vue frontend dashboard
3. Navigate to any dashboard page
4. Observe 401 Unauthorized errors

## Status: PENDING

## Priority: HIGH

## Recommendations
- Implement login screen in Vue dashboard for credential input
- Read `TASKER_API_KEY` environment variable in frontend
- Store API key securely (consider using localStorage with warnings)
- Add retry logic for 401 responses
- Ensure seamless integration with existing backend authentication
- Update documentation for frontend authentication setup