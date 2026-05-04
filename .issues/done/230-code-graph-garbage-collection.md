---
title: "Code Graph Stale Node Pruning (Garbage Collection)"
component: "Code-as-Graph"
priority: "HIGH"
status: "DONE"
version: "v1.0.0"
---

# Issue #230: Code Graph Stale Node Pruning

## Description
Clean up stale CodeFile and CodeSymbol nodes from the graph.

## Acceptance Criteria
- [x] Implement cleanup queries for stale nodes.
- [x] Ready for garbage collection integration.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add CLEANUP_STALE_NODES query to queries.py
- [x] Ready for integration in scan process

### Files Changed
- `queries.py`: Added cleanup queries
