# Issue #107: Implement API Authentication Middleware

## Description

The API currently has authentication middleware configured but not enforced. All endpoints are accessible without API key authentication, which is a security concern for production deployments.

## Requirements

- Enforce API key authentication on all non-public endpoints
- Add configurable authentication bypass for development mode
- Implement API key validation using TASKER_API_KEY environment variable
- Add proper 401/403 responses for unauthorized requests
- Add authentication status to health endpoint

## Technical Details

### Current State

The authentication middleware exists in `src/socialseed_tasker/entrypoints/web_api/app.py` at line ~106:
```python
async def api_key_auth_middleware(request: Request, call_next):
    # Currently not enforced - just logs the check
    return await call_next(request)
```

### Configuration
```python
# Environment variables
TASKER_API_KEY=your-secret-api-key  # Required for production
TASKER_AUTH_ENABLED=true/false      # Enable/disable authentication
```

### Implementation Steps
1. Make the middleware actually reject requests without valid API key
2. Add environment variable configuration for API key
3. Add development mode bypass (when AUTH_ENABLED=false)
4. Update health endpoint to show auth status
5. Add tests for authentication

### Protected Endpoints
All `/api/v1/*` endpoints should require authentication except:
- `/health` - Health check (can show auth status)
- `/docs` - OpenAPI docs (optional)
- `/openapi.json` - OpenAPI schema (optional)

### Expected Behavior After Fix
```python
# Without API key
GET /api/v1/issues
# Returns: 401 Unauthorized
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "API key required"
  }
}

# With valid API key
GET /api/v1/issues
X-API-Key: valid-key
# Returns: 200 OK
```

## Business Value

- Security for production deployments
- Prevent unauthorized access to data
- Audit trail for API access
- Compliance requirements

## Status: COMPLETED