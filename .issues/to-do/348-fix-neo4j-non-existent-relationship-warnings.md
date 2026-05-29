# Issue #348: Neo4j Warnings on Non-Existent Relationship Types and Properties

## Description
The `tasker status` command queries `CONTAINS` and `CODE_RELATIONSHIP` relationship types that don't exist in the graph, as well as a `language` property that doesn't exist on CodeFile nodes. Every `tasker status` call logs warnings in the console.

## Expected Behavior
The status query should only reference existing relationship types and properties to avoid polluting logs with warnings.

## Actual Behavior
Every `tasker status` call logs:
- `warn: relationship type does not exist. The relationship type 'CONTAINS' does not exist.`
- `warn: relationship type does not exist. The relationship type 'CODE_RELATIONSHIP' does not exist.`
- `warn: property key does not exist. The property 'language' does not exist.`

## Steps to Reproduce
1. Run `tasker status` in direct mode
2. Observe Neo4j notification warnings in the output

## Status: PENDING

## Priority: MEDIUM

## Component
GRAPH_ENGINE

## Suggested Fix
Update the Cypher query in the status command to use optional matches with existing relationship types (`DEFINES`, `IMPORTS`, `CALLS`) instead of `CONTAINS` and `CODE_RELATIONSHIP`. Remove or fix the reference to the `language` property if it hasn't been migrated to the schema.

## Impact
Cluttered logs with warnings. No functional impact, but reduces signal-to-noise ratio for debugging.
