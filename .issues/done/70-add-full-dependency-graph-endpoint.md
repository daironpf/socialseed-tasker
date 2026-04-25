# Issue #70: Add issue dependency chain visualization endpoint

## Description

The system has `GET /api/v1/issues/{id}/dependency-chain` which returns the transitive chain of dependencies for a single issue. However, there is no endpoint that returns the full project dependency graph for visualization purposes.

## Problem Found

The Kanban board and external tools cannot render a visual dependency graph of the entire project. The frontend would need to fetch each issue's chain individually and reconstruct the graph client-side.

## Impact

- Cannot show a project-level dependency graph in the UI
- External visualization tools (Mermaid, Graphviz) cannot consume the data
- Users cannot see the "big picture" of project dependencies

## Suggested Fix

- Add `GET /api/v1/graph/dependencies?project=shoe-ecommerce` endpoint
- Return nodes (issues with component info) and edges (dependency relationships)
- Support formats: JSON (default), Mermaid markdown, DOT (Graphviz)
- Include issue status and priority in node data for visual encoding
- Example response: `{"nodes": [{"id": "...", "title": "...", "component": "...", "status": "OPEN"}], "edges": [{"from": "...", "to": "..."}]}`

## Priority

MEDIUM

## Labels

api, feature, visualization
