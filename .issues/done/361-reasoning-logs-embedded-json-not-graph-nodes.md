# Issue #361: Reasoning logs stored as embedded JSON instead of standalone graph nodes with relationships

## Description
When `tasker reasoning log` is executed, the reasoning data is stored as a JSON array inside the Issue node's `reasoningLogs` property, rather than as standalone `ReasoningLog` nodes with proper graph relationships. This prevents graph traversal queries from finding reasoning traces, and makes it impossible to query across reasoning logs (e.g., "find all reasoning by this agent").

## Expected Behavior
Reasoning logs should be stored as `(:ReasoningLog)` nodes with:
- `(Agent)-[:PRODUCED]->(ReasoningLog)` — who created it
- `(ReasoningLog)-[:ABOUT]->(Issue)` — what issue it refers to
- Independent query-able properties (timestamp, context, reasoning text, files modified)

## Actual Behavior
Reasoning logs are serialized as JSON into `Issue.reasoningLogs`. No dedicated nodes or relationships exist.

## Steps to Reproduce
1. Run `tasker reasoning log --issue <id> --thought "..."` 
2. Query Neo4j: `MATCH (r:ReasoningLog) RETURN r` — returns 0 results
3. Query `MATCH (i:Issue) RETURN i.reasoningLogs` — shows JSON embedded in issue

## Status: PENDING

## Priority: HIGH

## Component
GRAPH_ENGINE

## Suggested Fix
Create standalone `ReasoningLog` nodes with:
- Properties: id, timestamp, context, reasoning, files_modified
- Relationships: `(Agent)-[:PRODUCED]->(ReasoningLog)-[:ABOUT]->(Issue)`

## Impact
Reasoning logs cannot be queried via graph traversal, reducing traceability and audit capabilities. RAG features cannot access reasoning context.
