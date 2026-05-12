# Issue #279: Cannot access API from Windows host

## Description
API responds correctly from inside container (port 8888) but cannot be accessed from Windows host using curl/Invoke-WebRequest. Connection is refused.

## Expected Behavior
API should be accessible from Windows host via localhost:8888

## Actual Behavior
- Inside container: `curl http://127.0.0.1:8888/health` returns 200 OK
- From Windows host: `Invoke-WebRequest http://localhost:8888/health` fails with connection refused
- Docker port mapping shows: `0.0.0.0:8888->8000/tcp`

## Steps to Reproduce
1. Start Docker services with docker-compose
2. Try to access API from Windows PowerShell: `Invoke-WebRequest http://localhost:8888/health`
3. Observe connection refused error

## Status: DONE

## Resolution
Updated docker-compose.yml to use explicit IPv4 binding (127.0.0.1:8888:8000) and added `extra_hosts` for Docker Desktop Windows compatibility. This ensures the API is accessible from the Windows host via localhost:8888.

## Priority: MEDIUM

## Component
Docker/Network (Infrastructure)

## Suggested Fix
Investigate Windows host networking configuration. This may require:
- Checking Docker Desktop network settings on Windows
- Verifying port binding configuration in docker-compose
- Testing with different network modes

## Impact
Black-box testing from Windows host requires workarounds (using CLI inside container). Limits ability to run external test scripts.

## Related Issues
- Related to Real-Test evaluation workflow (2026-05-12)