# Issue #101: Fix API Version Mismatch in Health Endpoint

## Description

The health endpoint returns version "0.5.0" while the project is actually at version "0.8.0". This causes version confusion for clients and monitoring systems.

## Requirements

- Update the version in the health endpoint response to match the actual project version (0.8.0)
- Ensure version is consistent across all API metadata
- Consider using dynamic version from package metadata

## Technical Details

### Current Response
```json
GET /health
{
  "status": "healthy",
  "version": "0.5.0"
}
```

### Expected Response
```json
GET /health
{
  "status": "healthy",
  "version": "0.8.0"
}
```

### Location of Version
The version is hardcoded in `src/socialseed_tasker/entrypoints/web_api/app.py` at line 61:
```python
app = FastAPI(
    ...
    version="0.6.0",  # This needs to be updated to 0.8.0
    ...
)
```

### Solution Approach
1. Read version from `pyproject.toml` or `__version__` in `__init__.py`
2. Make it configurable via environment variable
3. Update hardcoded value to "0.8.0"

## Business Value

Correct version reporting helps with:
- Deployment tracking
- Client compatibility checks
- Monitoring and logging
- Debugging version-specific issues

## Status: COMPLETED