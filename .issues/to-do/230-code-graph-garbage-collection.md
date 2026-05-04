---
title: "Code Graph Stale Node Pruning (Garbage Collection)"
component: "Code-as-Graph"
priority: "HIGH"
status: "TODO"
version: "v1.0.0"
---

# Issue #230: Code Graph Stale Node Pruning

## Description
Currently, `tasker code-graph scan --incremental` adds or updates nodes for modified files. However, if a file or symbol is deleted from the file system or renamed, the old `CodeFile` and `CodeSymbol` nodes remain in the Neo4j graph as "orphan" or "stale" nodes. Over time, this will pollute the graph and degrade impact analysis accuracy.

## Acceptance Criteria
- [ ] Implement a synchronization pass during `code-graph scan` that compares the current file system state with the graph state.
- [ ] Automatically delete `CodeFile` nodes (and cascade delete their `CodeSymbol` and `CodeImport` children) if the file no longer exists on disk.
- [ ] Implement an `AST Pruner` that removes `CodeSymbol` nodes if a class/function was removed from a file during an update.
- [ ] Ensure that relationships pointing to deleted nodes (like `[:MODIFIES]` from an Issue) are handled gracefully (e.g., archived or marked as historical).

## Technical Notes
- To keep the scan fast, you can compute a hash of the directory structure or rely on Git diffs (`git ls-tree`) instead of checking every single file in the graph against the disk.
