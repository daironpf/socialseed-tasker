GraphViz and Impact Analysis Guide

Endpoints
- GET /api/v1/graph returns graph JSON
- GET /api/v1/graph/impact/{node_id}?max_depth=5 returns impact list
- GET /api/v1/graph/export.json returns graph JSON export
- GET /api/v1/graph/export.svg returns a simple SVG export
- UI: /graphviz

CLI
- python -m socialseed_tasker.graphviz.cli build --out graph.json
- python -m socialseed_tasker.graphviz.cli impact --node <id> --out impact.json --max-depth 5
- python -m socialseed_tasker.graphviz.cli export-svg --out graph.svg

Running
- Local dev:
  docker compose -f docker-compose.graphviz.yml up -d --build
- Programmatic:
  Use build_graph(container) and compute_impact(graph, node_id, max_depth)

Notes
- Graph building is deterministic: nodes and edges are sorted by id.
- Real-time updates: graphviz subscribes to EventBus events and publishes graph.updated events.
