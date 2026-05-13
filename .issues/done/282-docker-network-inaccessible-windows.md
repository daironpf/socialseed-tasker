# Issue #282: Docker container ports inaccessible from Windows host

## Description
Docker container ports are not accessible from Windows host. API runs inside container but external connections fail with "Empty reply from server" or connection errors.

## Expected Behavior
Docker containers should be accessible from Windows host via mapped ports.

## Actual Behavior
- curl connects but gets empty response
- Python urllib/requests fail with ConnectionAbortedError
- API logs show successful GET requests when tested from inside container
- TCP connection test passes (port is open)

## Steps to Reproduce
1. Run `docker compose up -d` in real-test/.agent/
2. Verify containers are running: `docker compose ps`
3. Try to access API from Windows host: `curl http://localhost:8888/api/v1/components`
4. Observe: Empty response despite connection being accepted

## Status: COMPLETED

## Priority: HIGH

## Component
DOCKER

## Suggested Fix
- Investigate Windows Docker networking configuration
- Check if Hyper-V or Windows Firewall is blocking
- Consider using host network mode or different port mapping
- Alternative: Use Docker Desktop's internal DNS resolution

## Impact
Cannot execute black-box testing from Windows host. All Real-Test workflows fail on this platform.

## Related Issues
- Related to Real-Test evaluation workflow (2026-05-13)
- FIND-001 from report.md