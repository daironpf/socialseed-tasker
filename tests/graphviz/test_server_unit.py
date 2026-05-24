from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from socialseed_tasker.graphviz.server import app


@patch("socialseed_tasker.graphviz.server.build_default_container")
def test_graph_api(mock_build):
    container = MagicMock()
    container.issue_repo.list.return_value = [
        MagicMock(id="i1", title="T1"),
        MagicMock(id="i2", title="T2"),
    ]
    mock_build.return_value = container
    client = TestClient(app)
    r = client.get("/api/v1/graph")
    assert r.status_code == 200
    j = r.json()
    assert "nodes" in j
    assert "edges" in j
    assert len(j["nodes"]) == 2


@patch("socialseed_tasker.graphviz.server.build_default_container")
def test_graph_api_impact(mock_build):
    container = MagicMock()
    container.issue_repo.list.return_value = [
        MagicMock(id="i1", title="T1"),
        MagicMock(id="i2", title="T2"),
        MagicMock(id="i3", title="T3"),
    ]
    mock_build.return_value = container
    client = TestClient(app)
    r = client.get("/api/v1/graph/impact/i1")
    assert r.status_code == 200
    j = r.json()
    assert j["node"] == "i1"


@patch("socialseed_tasker.graphviz.server.build_default_container")
def test_graph_api_impact_not_found(mock_build):
    container = MagicMock()
    container.issue_repo.list.return_value = []
    mock_build.return_value = container
    client = TestClient(app)
    r = client.get("/api/v1/graph/impact/nonexistent")
    assert r.status_code == 404


@patch("socialseed_tasker.graphviz.server.build_default_container")
def test_graph_api_export_json(mock_build):
    container = MagicMock()
    container.issue_repo.list.return_value = [
        MagicMock(id="i1", title="T1"),
    ]
    mock_build.return_value = container
    client = TestClient(app)
    r = client.get("/api/v1/graph/export.json")
    assert r.status_code == 200
    assert "nodes" in r.json()


@patch("socialseed_tasker.graphviz.server.build_default_container")
def test_graph_api_export_svg(mock_build):
    container = MagicMock()
    container.issue_repo.list.return_value = [
        MagicMock(id="i1", title="T1"),
    ]
    mock_build.return_value = container
    client = TestClient(app)
    r = client.get("/api/v1/graph/export.svg")
    assert r.status_code == 200
    assert "image/svg+xml" in r.headers.get("content-type", "")


@patch("socialseed_tasker.graphviz.server.build_default_container")
def test_graph_viz_ui(mock_build):
    container = MagicMock()
    container.issue_repo.list.return_value = []
    mock_build.return_value = container
    client = TestClient(app)
    r = client.get("/graphviz")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
