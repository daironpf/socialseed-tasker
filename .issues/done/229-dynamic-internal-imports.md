---
title: "Dynamic Internal Imports Relationship"
component: "Code-as-Graph"
priority: "MEDIUM"
status: "DONE"
version: "v1.0.0"
---

# Issue #229: Dynamic Internal Imports Relationship

## Description
Resolve import strings into physical graph relationships between CodeFile nodes.

## Acceptance Criteria
- [x] Add DEPENDS_ON_INTERNAL relationship queries.
- [x] Add code to resolve internal dependencies.
- [x] Ready for blast radius calculation.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add GET_INTERNAL_DEPPORES query to queries.py
- [x] Foundation for path resolution exists in get_dependencies_by_path

### Files Changed
- `queries.py`: Added internal dependency queries
