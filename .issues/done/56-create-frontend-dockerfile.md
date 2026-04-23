# Issue #56: Create Dockerfile for Vue.js frontend

## Description

Create a multi-stage Dockerfile to build and serve the Vue.js frontend application with nginx.

### Requirements

- Multi-stage build: builder stage (Node.js) + serve stage (nginx)
- Install npm dependencies from package.json
- Build the Vue app with `npm run build`
- Serve static files with nginx on port 80
- Copy custom nginx configuration
- Add health check endpoint

### Technical Details

- Base images: node:20-alpine (builder), nginx:alpine (serve)
- Copy only built artifacts to final image (security, smaller size)
- Custom nginx.conf for Vue Router history mode and API proxy

### Expected File Paths

- `frontend/Dockerfile`
- `frontend/nginx.conf`

## Status: COMPLETED

## Implementation Notes

- Created frontend/Dockerfile with multi-stage build
- Created nginx.conf with:
  - Vue Router history mode (try_files $uri $uri/ /index.html)
  - API proxy to backend (/api/ -> http://api:8000/api/)
  - Gzip compression
  - Static asset caching
- Added .dockerignore to exclude node_modules, dist, .venv, etc.