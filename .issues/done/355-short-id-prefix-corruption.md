# Issue #355: Short ID prefix resolution creates corrupted Issue nodes instead of resolving

## Description
When `tasker issue close` receives an 8-char short prefix, instead of resolving it to the full UUID or reporting "not found", it creates a new Issue node with `id = "<short-prefix>"`, `title = NULL`, and missing `componentId`. This corrupts the data and breaks `issue list` because Pydantic validation fails on the malformed node.

This is different from the previous #350 bug (KeyError on missing property). This bug actively WRITES corrupted data to the database.

## Expected Behavior
Short prefix should either resolve to the full UUID before writing, or reject unknown prefixes with "not found".

## Actual Behavior
Creates corrupted Issue nodes in Neo4j with short IDs and NULL required fields.

## Steps to Reproduce
1. Create an issue (get its full UUID, e.g. abc12345-...)
2. Run `tasker issue close abc12345` (8-char prefix only)
3. Check Neo4j: `MATCH (i:Issue) WHERE size(i.id) < 30 RETURN i.id` — corrupted node exists
4. Run `tasker issue list` — fails with Pydantic validation error

## Status: PENDING

## Priority: CRITICAL

## Component
CLI / API

## Suggested Fix
The short ID resolution should happen before any write operations. If the short prefix cannot be resolved, abort with "not found" instead of writing a partial node.
