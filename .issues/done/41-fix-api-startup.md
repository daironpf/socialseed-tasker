# Issue #41: Fix API app factory and uvicorn startup

## Description

The FastAPI application cannot be started with uvicorn using the standard module path. The `app` attribute is not exported from the module, only the factory function `create_app` is available.

### Requirements

- Make the API startable with: `uvicorn socialseed_tasker.entrypoints.web_api.app:app`
- Ensure the repository is properly initialized with configuration from environment variables
- Add a `__main__.py` for direct execution: `python -m socialseed_tasker.entrypoints.web_api`

### Technical Details

Error when running `uvicorn socialseed_tasker.entrypoints.web_api.app:app`:
```
Error loading ASGI app. Attribute "app" not found in module "socialseed_tasker.entrypoints.web_api.app"
```

The `app.py` only exports `create_app` function, not a ready-to-use app instance.

Also, the factory function requires a repository to be passed, but when starting with uvicorn directly, no repository is provided. Need to handle this case.

### Solution

1. Create `src/socialseed_tasker/entrypoints/web_api/__main__.py` that:
   - Loads config from environment
   - Creates Container and gets repository
   - Calls create_app with repository
   - Runs with uvicorn

**Resolution**: Created `__main__.py` that properly initializes the container and creates the app with repository.

## Status: COMPLETED