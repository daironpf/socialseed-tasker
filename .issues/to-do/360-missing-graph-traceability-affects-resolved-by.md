# Issue #360: No AFFECTS or RESOLVED_BY relationships created between closed Issues and CodeSymbols/Commits

## Description
After implementing issues with code files and running `code-graph scan`, the Neo4j graph has CodeSymbol nodes (75 symbols from 10 files) and reasoning logs stored as JSON in Issue nodes, but there are ZERO relationships connecting them:
1. No `(Issue)-[:AFFECTS]->(CodeSymbol)` relationships exist linking closed issues to the code they implemented.
2. No `(Issue)-[:RESOLVED_BY]->(Commit)` relationships linking issues to git commits.
3. Reasoning logs are stored as embedded JSON arrays inside Issue nodes (`reasoningLogs` property) rather than as separate `ReasoningLog` nodes with `(Agent)-[:PRODUCED]->(ReasoningLog)` and `(Issue)-[:HAS_REASONING]->(ReasoningLog)` relationships.

## Expected Behavior
Closed issues should be linked to the code symbols they affected, the commits that resolved them, and have proper graph relationships to reasoning logs.

## Actual Behavior
Closed issues only have `BELONGS_TO` (component) and `DEPENDS_ON` (other issues) relationships. CodeSymbols, Commits, and ReasoningLogs exist but are disconnected from issues.

## Steps to Reproduce
1. Create issues, implement code, run `code-graph scan src/`
2. Close issues via `tasker issue close`
3. Run `tasker reasoning log` for each issue
4. Query Neo4j: `MATCH (i:Issue)-[:AFFECTS]->(c:CodeSymbol) RETURN ...` — returns 0 results

## Status: PENDING

## Priority: HIGH

## Component
GRAPH_ENGINE

## Suggested Fix
1. When closing an issue, auto-create `RESOLVED_BY` relationship to current git HEAD commit
2. When running `code-graph scan`, create `AFFECTS` relationships for files modified by the issue
3. Store reasoning logs as standalone `ReasoningLog` nodes with proper relationships

## Impact
The graph is incomplete — traceability from requirements to code is broken, reducing the value of impact analysis and RAG features.
