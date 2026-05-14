# Issue #285: Docker Desktop Windows Port Binding Configuration

## Description
Docker Desktop on Windows requires specific port binding configuration for containers to be accessible from the Windows host. The standard port mapping `9000:8000` does not work reliably, requiring explicit `127.0.0.1:9000:8000` binding format.

## Expected Behavior
Docker containers should be accessible from Windows host using standard port mappings.

## Actual Behavior
Port mapping `9000:8000` results in "Connection refused" errors from Windows host, even though the port is listening (verified with netstat). Using `127.0.0.1:9000:8000` binding format resolves the issue.

## Steps to Reproduce
1. Create docker-compose.yml with `ports: - "9000:8000"`
2. Start services: `docker-compose up -d`
3. Verify port is listening: `netstat -ano | Select-String ":9000"`
4. Try to connect from Windows: `Invoke-WebRequest -Uri "http://localhost:9000/health"`
5. Observe: "Connection terminated unexpectedly"

## Status: PENDING

## Priority: MEDIUM

## Component
Infrastructure / Docker Networking

## Suggested Fix
- Update docker-compose.yml template to use `127.0.0.1:9000:8000` format
- Document Windows Docker Desktop networking requirements
- Add troubleshooting section for common Windows Docker networking issues

## Impact
- Black-box testing from Windows host requires specific configuration
- Phase 4 implementation testing cannot be performed without this workaround
- Increased setup friction for Windows users