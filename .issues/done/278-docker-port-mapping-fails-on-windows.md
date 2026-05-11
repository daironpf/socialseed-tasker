# Issue #278: Docker Port Mapping Fails on Windows

## Description
Docker port mapping (8000, 8080) fails with "bind: permission denied" error on Windows when running `docker-compose up -d`. The API and frontend services cannot start properly due to this issue.

## Expected Behavior
Docker should successfully map container ports to host ports (8000 -> 8000, 8080 -> 8080) without permission errors.

## Actual Behavior
Error: "Error response from daemon: ports are not available: exposing port TCP 0.0.0.0:8000 -> 127.0.0.1:0: listen tcp 0.0.0.0:8000: bind: Intento de acceso a un socket no permitido por sus permisos de acceso."

## Steps to Reproduce
1. Run `docker-compose up -d` in a Windows environment
2. Observe port binding error for ports 8000 and 8080

## Status: COMPLETED

## Priority: HIGH

## Component
DOCKER

## Suggested Fix
1. Update docker-compose.yml to use alternative ports (8888, 8889) as defaults
2. Document the Windows port conflict issue in the README
3. Add a pre-check script that detects port availability before starting services
4. Consider using host network mode as an alternative solution

## Impact
Users on Windows cannot use the default docker-compose setup. Requires manual port configuration or workaround (running API directly on host).

## Related Issues
- Previous related issue: #277 (API Endpoints Return 500 in Docker Container)