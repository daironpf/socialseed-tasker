# Issue #166: Frontend Authentication Handling

## Description
Implement proper authentication handling in the Vue frontend to work with `TASKER_AUTH_ENABLED=true` on the backend.

## Expected Behavior
The Vue dashboard should handle 401 Unauthorized errors gracefully with a login screen or API key configuration.

## Actual Behavior
The frontend breaks with 401 errors when backend authentication is enabled.

## Status: DONE ✓ (duplicate of #155)

## Resolution
- Already resolved in #155: LoginScreen + authStore implemented

## Steps to Reproduce
1. Set `TASKER_AUTH_ENABLED=true` on backend
2. Start the Vue frontend
3. Navigate to any dashboard page
4. Observe 401 Unauthorized errors

## Status: PENDING

## Priority: HIGH

## Recommendations
This is covered by Issue #06. See Issue #06-frontend-authentication.md for detailed requirements.

## Related Issues
- Issue #06: Frontend Authentication (covers the Vue dashboard login)