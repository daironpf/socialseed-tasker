# Issue #121: Add Health Check for Sync Dependencies

## Description

Add health check verification for sync dependencies (httpx) so the service reports healthy status instead of crashing.

## Current State

- Sync service imports httpx in check_connectivity()
- If httpx fails to import, entire endpoint crashes with INTERNAL_ERROR
- No graceful fallback

## Problem

```
GET /api/v1/status
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

## Root Cause

- httpx not in runtime dependencies (FIXED in #119)
- No try/except around import
- No health check to verify dependencies

## Requirements

- Add health check at /health that verifies httpx is available
- Add try/except around import httpx in sync_engine.py
- Add graceful fallback when httpx unavailable

## Implementation

```python
# In sync_engine.py
def check_connectivity(self) -> bool:
    try:
        import httpx  # Already imported
        response = httpx.get("https://api.github.com", timeout=5.0)
        return response.status_code == 200
    except ImportError:
        logger.warning("httpx not available, sync limited")
        return False
    except Exception as e:
        logger.error(f"Sync connectivity check failed: {e}")
        return False
```

## Status: COMPLETED