# Issue #122: Add Admin Endpoint Authentication

## Description

Add authentication requirement for admin endpoints like /admin/reset to prevent unauthorized data manipulation.

## Current State

- /api/v1/admin/reset is accessible without authentication
- Anyone can clear all data
- No protection on admin operations

## Problem

```
POST /api/v1/admin/reset?scope=all
Returns: 200 OK
No authentication required!
```

## Requirements

- Add API key authentication for admin endpoints
- Use same mechanism as main API authentication
- Return 401 for unauthorized requests

## Implementation

```python
# In routes.py - add dependency
def require_admin(api_key: str = Query(...)):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

## Status: COMPLETED