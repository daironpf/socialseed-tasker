# Issue #359: Cypher queries reference labels that don't exist in Neo4j schema

## Description
Commands like `tasker constraints list` run `MATCH (c:Constraint) RETURN c` but the `Constraint` label doesn't exist in the schema. This produces WARNING-level Neo4j notifications that clutter the output.

## Expected Behavior
Queries should not produce schema warnings.

## Actual Behavior
Each run of `tasker constraints list` produces: `warn: label does not exist. The label 'Constraint' does not exist.`

## Steps to Reproduce
1. Run `tasker constraints list`
2. Check output for "label does not exist" warning

## Status: PENDING

## Priority: LOW

## Component
GRAPH_ENGINE

## Suggested Fix
Add schema initialization for Constraint nodes, or modify the query to handle non-existent labels gracefully.

## Impact
Cluttered output makes it harder to read command results.
