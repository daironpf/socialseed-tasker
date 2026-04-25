# Issue #66: Add Neo4j connection status to health endpoint

## Description

The `/health` endpoint only returns `{"status": "healthy", "version": "0.5.0"}` without actually checking if Neo4j is reachable. A user could see "healthy" while the database is down.

## Problem Found

The health endpoint is a simple hardcoded dict return. It does not ping Neo4j to verify connectivity. During testing, the API reported healthy even when Neo4j was being restarted.

## Impact

- False sense of system health
- Cannot use health checks for proper Docker/K8s liveness probes
- Monitoring systems cannot detect database connectivity issues

## Suggested Fix

- Add Neo4j connectivity check to health endpoint (simple `RETURN 1` query)
- Return detailed status: `{"status": "healthy", "version": "0.5.0", "neo4j": "connected", "neo4j_uri": "bolt://localhost:7687"}`
- Return `status: "degraded"` if Neo4j is unreachable but API is up
- Add separate `/health/ready` and `/health/live` endpoints for Kubernetes

## Priority

HIGH

## Labels

api, reliability, monitoring
