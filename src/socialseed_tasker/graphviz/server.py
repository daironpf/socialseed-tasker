from __future__ import annotations

from contextlib import suppress
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response

from socialseed_tasker.cli.wiring import build_default_container
from socialseed_tasker.events.serializers import EventDTO
from socialseed_tasker.graphviz.builder import build_graph, compute_impact

router = APIRouter(prefix="/api/v1/graph", tags=["graphviz"])


def get_container():
    return build_default_container()


@router.get("", response_class=JSONResponse)
def api_get_graph(container: Any = None):
    container = container or get_container()
    g = build_graph(container)
    return g.to_json()


@router.get("/impact/{node_id}", response_class=JSONResponse)
def api_get_impact(node_id: str, max_depth: int = 5, container: Any = None):
    container = container or get_container()
    g = build_graph(container)
    if node_id not in g.nodes:
        raise HTTPException(status_code=404, detail="node not found")
    impacted = compute_impact(g, node_id, max_depth=max_depth)
    return {"node": node_id, "impact": impacted}


@router.get("/export.json", response_class=JSONResponse)
def api_export_json(container: Any = None):
    container = container or get_container()
    g = build_graph(container)
    return g.to_json()


@router.get("/export.svg")
def api_export_svg(container: Any = None):
    container = container or get_container()
    g = build_graph(container)
    nodes = g.to_json()["nodes"]
    edges = g.to_json()["edges"]
    width = 800
    y_step = 40
    svg_lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}">']
    id_to_y: dict[str, int] = {}
    for idx, n in enumerate(nodes):
        y = 20 + idx * y_step
        id_to_y[n["id"]] = y
        svg_lines.append(f'<text x="10" y="{y}" font-family="monospace">{n["id"]}: {n["label"]}</text>')
    for e in edges:
        y1 = id_to_y.get(e["from"], 0)
        y2 = id_to_y.get(e["to"], 0)
        svg_lines.append(
            f'<line x1="200" y1="{y1 - 5}" x2="400" y2="{y2 - 5}" '
            f'stroke="black" marker-end="url(#arrow)"/>'
        )
    svg_lines.append("</svg>")
    svg = "\n".join(svg_lines)
    return Response(content=svg, media_type="image/svg+xml")


UI_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Tasker GraphViz</title>
  <style>body{font-family:Arial} #graph{width:100%;height:80vh;border:1px solid #ccc}</style>
</head>
<body>
  <h2>Tasker Dependency Graph</h2>
  <div id="controls">
    Node ID: <input id="node" /> <button id="impact">Show Impact</button>
    <button id="refresh">Refresh Graph</button>
  </div>
  <pre id="graph"></pre>
  <script>
    async function fetchGraph(){ const r=await fetch('/api/v1/graph'); const j=await r.json(); document.getElementById('graph').textContent=JSON.stringify(j,null,2); }
    document.getElementById('refresh').addEventListener('click', fetchGraph);
    document.getElementById('impact').addEventListener('click', async ()=>{ const id=document.getElementById('node').value; const r=await fetch('/api/v1/graph/impact/'+encodeURIComponent(id)); const j=await r.json(); alert('Impact:\\n'+JSON.stringify(j,null,2)); });
    fetchGraph();
  </script>
</body>
</html>
"""

app = FastAPI(title="Tasker GraphViz", version="0.1.0")
app.include_router(router)


@app.get("/graphviz", response_class=HTMLResponse)
def ui():
    return UI_HTML


@app.on_event("startup")
def startup_subscribe():
    container = build_default_container()
    eb = getattr(container, "events_bus", None)
    if eb:

        def handler(evt: EventDTO) -> None:
            with suppress(Exception):
                container.events_bus.publish(
                    EventDTO(
                        id=evt.id,
                        type="graph.updated",
                        source="graphviz",
                        payload={"source": "graphviz"},
                        created_at=evt.created_at,
                    )
                )

        eb.subscribe("issue.created", handler)
        eb.subscribe("dependency.added", handler)
        eb.subscribe("issue.updated", handler)
