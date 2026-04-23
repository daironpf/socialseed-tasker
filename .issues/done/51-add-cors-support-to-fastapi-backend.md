# Issue #51: Add CORS support to FastAPI backend for Vue frontend

## Description

Configure CORS (Cross-Origin Resource Sharing) on the FastAPI backend so the Vue.js frontend running on a different port (5173) can make API requests to the backend (8000).

### Requirements

- Add `CORSMiddleware` to the FastAPI app in `app.py`
- Configure allowed origins:
  - `http://localhost:5173` (Vite dev server)
  - `http://127.0.0.1:5173`
  - Make it configurable via environment variable `ALLOWED_ORIGINS` (comma-separated)
- Allow all methods (GET, POST, PATCH, DELETE, OPTIONS)
- Allow all headers
- Allow credentials

### Technical Details

- Use `fastapi.middleware.cors.CORSMiddleware`
- Configuration via environment variable to support production deployments
- Development default: `http://localhost:5173,http://127.0.0.1:5173`

### Expected File Paths

- Modify `src/socialseed_tasker/entrypoints/web_api/app.py`
- May need to update `src/socialseed_tasker/bootstrap/container.py` if config needs new field

### Business Value

Without CORS, the browser will block all API requests from the Vue frontend to the FastAPI backend, making the web UI completely non-functional.

## Status: COMPLETED
