# Issue #402: Add tests for health endpoint Neo4j connection tracking

## Description

The `/health` endpoint correctly tracks Neo4j connection status, transitioning through states: `healthy` → `degraded` (neo4j: disconnected) → `healthy` (neo4j: connected). This behavior should be covered by automated tests.

## Expected Behavior

Health endpoint accurately reflects Neo4j connection state in real-time.

## Actual Behavior

Works correctly — tested with DB stop/start cycle.

## Steps to Reproduce
1. Check `/health` → `{"status":"healthy","neo4j":"connected"}`
2. Stop Neo4j → `/health` → `{"status":"degraded","neo4j":"disconnected"}`
3. Start Neo4j → `/health` → `{"status":"healthy","neo4j":"connected"}`

## Status: PENDING

## Priority: LOW

## Component
API / Testing

## Suggested Fix
Add integration tests that verify health state transitions across DB restarts.

## Impact
Ensures monitoring tools can rely on health endpoint accuracy.
