---
title: "Dynamic Internal Imports Relationship"
component: "Code-as-Graph"
priority: "MEDIUM"
status: "TODO"
version: "v1.0.0"
---

# Issue #229: Dynamic Internal Imports Relationship

## Description
In the current `Code-as-Graph` model, `CodeImport` nodes store the imported module as a simple String property (`module`). This limits graph traversals across file boundaries. We need to resolve these import strings into physical graph relationships between `CodeFile` nodes representing internal dependencies.

## Acceptance Criteria
- [ ] Implement an AST resolution step during `tasker code-graph scan`.
- [ ] If an imported `module` matches another `CodeFile` in the graph, create a direct `(CodeFile)-[:DEPENDS_ON_INTERNAL]->(CodeFile)` relationship.
- [ ] Update `GRAPH_MODEL.md` to document the `[:DEPENDS_ON_INTERNAL]` relationship.
- [ ] Provide a CLI command (e.g., `tasker code-graph deps <file>`) to visualize the resolved file-level dependency tree.
- [ ] Ensure that `CodeImport` nodes are still maintained for external/third-party dependencies.

## Technical Notes
- Resolving imports requires matching the import path string to the physical file path logic (e.g., in Python, translating `src.core.module` to `src/core/module.py`).
- This enhances the "Blast Radius" calculation, allowing the Agent to instantly know which files depend on the one they are modifying.
