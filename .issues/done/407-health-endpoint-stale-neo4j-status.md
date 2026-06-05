# Issue #407: Health endpoint shows stale Neo4j status after container stop

## Description
`GET /health` returns `{"status": "healthy", "neo4j": "connected"}` even after stopping the Neo4j container with `docker stop tasker-tasker-db-1`. The health endpoint caches the last known state and does not periodically re-verify connectivity.

## Expected Behavior
- Within a reasonable timeout (e.g., 5–10s), the health endpoint should detect the Neo4j outage.
- `neo4j` field should show `"disconnected"` or `"degraded"`.
- HTTP status code could remain 200 (degraded) or switch to 503 (unhealthy).

## Actual Behavior
```json
{
  "status": "healthy",
  "neo4j": "connected"
}
```
HTTP 200, even with DB down for minutes.

## Steps to Reproduce
1. `docker stop tasker-tasker-db-1`
2. `curl http://localhost:8888/health`
3. Observe `neo4j: connected` despite container being stopped

## Status: PENDING

## Priority: MEDIUM

## Component
API / Health / Monitoring

## Suggested Fix
Replace the cached health check with a real-time verification. On each `/health` request, attempt a lightweight Neo4j query (e.g., `RETURN 1`) with a short timeout. Only return `"connected"` if the query succeeds.

## Impact
- Monitoring systems (Docker healthchecks, load balancers) may not detect DB failures.
- Cascading failures harder to diagnose.
