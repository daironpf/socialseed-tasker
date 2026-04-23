# Issue #38: Fix API startup module reference

## Description

The FastAPI application cannot be started with `uvicorn socialseed_tasker.entrypoints.web_api.app:app` because there is no `app` variable in the module.

### Error

```
ERROR:    Error loading ASGI app. Attribute "app" not found in module "socialseed_tasker.entrypoints.web_api.app".
```

### Current state

The module exports a factory function `create_app(repository)` instead of an app instance, which requires passing a repository.

### Expected behavior

Users should be able to start the API with:
```bash
uvicorn socialseed_tasker.entrypoints.web_api.app:app --host 0.0.0.0 --port 8000
```

Or there should be a documented way to run the API.

### Solution options

1. Export a default app instance with file repository
2. Create a separate module `api.py` that exports the ready-to-use app
3. Update documentation with the correct startup command

## Status: PENDING
