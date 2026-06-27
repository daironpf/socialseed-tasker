# Issue #184: Windows Host Network Inaccessibility

## Description
The API container starts successfully and responds to health checks from within the container, but the exposed ports (8888, 8889) are not accessible from the Windows host. The httpx library receives "Server disconnected without sending a response" errors when trying to connect to localhost:8888.

## Expected Behavior
API should be accessible from Windows host at http://localhost:8888

## Actual Behavior
API only works from inside the container via `docker exec`. Windows host receives "Server disconnected without sending a response".

## Steps to Reproduce
1. Start services: `docker-compose up -d`
2. Verify container is running: `docker ps`
3. Try to access API from Windows: `httpx.get('http://localhost:8888/health')`
4. Observe error: RemoteProtocolError: Server disconnected without sending a response
5. Verify API works inside container: `docker exec tasker-api python -c "import httpx; print(httpx.get('http://127.0.0.1:8888/health').status_code)"` returns 200

## Status: COMPLETED

## Resolution
The issue was resolved by changing the port mapping from 8888 to 9000 in docker-compose.yml. This is likely due to a conflict or Windows-specific issue with port 8888 in Docker Desktop.

**Solution Applied:**
- Changed port mapping from `8888:8000` to `9000:8888` in docker-compose.yml
- API is now accessible at http://localhost:9000 from Windows host
- Neo4j connection uses `host.docker.internal:7687` for cross-network communication

**Verified:**
- http://localhost:9000/health returns 200
- http://localhost:8889 (frontend) continues to work

## Priority: HIGH

## Component
Infrastructure / Docker Networking

## Suggested Fix
- Investigate Docker Desktop network configuration for Windows
- Check Windows firewall rules that might block port mapping
- Consider using different network mode (host network)
- Document the issue as known limitation for Windows environments
- Alternative: Use Linux-based CI/CD environment for full black-box testing

## Impact
- Black-box testing cannot be performed from Windows host
- Phase 4 (Implementation & Doc-Sync) cannot be executed as designed
- Workaround required: Use `docker exec` to interact with API

## Related Issues
- Previous setup friction issues in .issues/done/183-reduce-setup-friction.md