# Issue #216: Enhanced Impact Analysis

## Description

Enhance the current impact analysis capabilities by leveraging the new Code-as-Graph features and deeper graph queries, ensuring more accurate risk levels and dependency impact mapping.

## Problem

The current impact analysis uses basic BFS traversing through components. With the introduction of Code-as-Graph and deeper reasoning logs, the impact analysis needs to be more granular (down to the file/function level) to accurately gauge the risk of changes.

## Expected Behavior

The impact analysis should:
- Support file and function-level dependency analysis using Code-as-Graph data
- Identify transitive impacts accurately through code structures, not just issue/component boundaries
- Provide a clear, granular risk level calculation
- Allow integration with RAG to find historically similar impact scopes

## Technical Implementation

### Graph Traversal Enhancements
- Integrate `[:CALLS]` and `[:DEPENDS_ON]` relationships from Code-as-Graph into the impact calculation
- Calculate risk based on function/class centrality

### API & CLI Updates
- Update existing `analyze` endpoints and CLI commands to optionally include deep code impact
- Return specific files/functions affected in the analysis payload

## Status

**COMPLETED**

## Priority

**MEDIUM** - Enhances v0.9.0 capabilities

## Component

CORE, ANALYSIS, API

## Acceptance Criteria

- [x] Update impact analysis Cypher queries to leverage Code-as-Graph nodes
- [x] Enhance risk level calculation logic with code-level granularity
- [x] Update CLI command `tasker analyze impact` output format
- [x] Update API endpoint `/api/v1/analyze/impact` response schema
- [x] Unit tests for enhanced impact analysis

## Related Issues

- #208 - Code-as-Graph with Tree-sitter
- #211 - Code Graph CLI and API Commands