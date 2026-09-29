from __future__ import annotations

from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import mcp as mcp_module
from socialseed_tasker.infrastructure.web_api.routers.mcp import MCPRegistry


def _client() -> TestClient:
    return TestClient(create_app())


def test_mcp_register_and_list_servers():
    client = _client()
    resp = client.post(
        "/api/v1/mcp/servers",
        json={
            "name": "neo4j-mcp",
            "transport": "http",
            "url": "http://mcp.local:8080",
            "tools": ["rag_search", "rag_stats"],
        },
    )
    assert resp.status_code == 200
    created = resp.json()["data"]
    assert created["id"].startswith("srv-")
    assert created["name"] == "neo4j-mcp"
    assert created["tools"] == ["rag_search", "rag_stats"]
    assert created["status"] == "online"
    assert created["lastSeen"]

    resp = client.post(
        "/api/v1/mcp/servers",
        json={"id": created["id"], "name": "neo4j-mcp", "status": "offline"},
    )
    assert resp.status_code == 200

    resp = client.get("/api/v1/mcp/servers")
    assert resp.status_code == 200
    servers = resp.json()["data"]
    assert len(servers) == 1
    assert servers[0]["status"] == "offline"


def test_mcp_upsert_session_and_heartbeat():
    client = _client()
    resp = client.post(
        "/api/v1/mcp/sessions",
        json={"id": "sess-1", "clientName": "tasker-ui", "clientType": "web"},
    )
    assert resp.status_code == 200
    session = resp.json()["data"]
    assert session["id"] == "sess-1"
    assert session["status"] == "active"
    assert session["uptime"] >= 0
    assert session["contextLimit"] == 524288
    connected_at = session["connectedAt"]

    resp = client.post(
        "/api/v1/mcp/sessions",
        json={"id": "sess-1", "clientName": "tasker-ui", "contextConsumed": 4096},
    )
    assert resp.status_code == 200

    resp = client.get("/api/v1/mcp/sessions")
    sessions = resp.json()["data"]
    assert len(sessions) == 1
    assert sessions[0]["connectedAt"] == connected_at
    assert sessions[0]["contextConsumed"] == 4096
    assert sessions[0]["uptime"] >= 0


def test_mcp_delete_session():
    client = _client()
    client.post("/api/v1/mcp/sessions", json={"id": "sess-x", "clientName": "cli"})
    resp = client.delete("/api/v1/mcp/sessions/sess-x")
    assert resp.status_code == 200
    assert resp.json()["data"] == {"id": "sess-x"}
    assert client.get("/api/v1/mcp/sessions").json()["data"] == []
    resp = client.delete("/api/v1/mcp/sessions/sess-x")
    assert resp.status_code == 404


def test_mcp_record_and_filter_tool_calls():
    client = _client()
    resp = client.post(
        "/api/v1/mcp/tool-calls",
        json={"tool": "rag_search", "sessionId": "sess-1", "server": "neo4j-mcp"},
    )
    assert resp.status_code == 200
    call = resp.json()["data"]
    assert call["id"].startswith("call-")
    assert call["status"] == "running"
    assert call["startedAt"]

    client.post(
        "/api/v1/mcp/tool-calls",
        json={"tool": "rag_stats", "status": "success", "durationMs": 12},
    )

    calls = client.get("/api/v1/mcp/tool-calls").json()["data"]
    assert len(calls) == 2
    assert calls[0]["tool"] == "rag_stats"

    calls = client.get("/api/v1/mcp/tool-calls", params={"tool": "rag_search"}).json()["data"]
    assert len(calls) == 1
    assert calls[0]["sessionId"] == "sess-1"

    calls = client.get("/api/v1/mcp/tool-calls", params={"status": "success"}).json()["data"]
    assert len(calls) == 1
    assert calls[0]["tool"] == "rag_stats"

    resp = client.get("/api/v1/mcp/tool-calls", params={"limit": 0})
    assert resp.status_code == 422


def test_mcp_tool_call_update_does_not_duplicate():
    client = _client()
    resp = client.post(
        "/api/v1/mcp/tool-calls",
        json={"id": "call-fixed", "tool": "rag_search"},
    )
    assert resp.json()["data"]["status"] == "running"

    resp = client.post(
        "/api/v1/mcp/tool-calls",
        json={
            "id": "call-fixed",
            "tool": "rag_search",
            "status": "success",
            "durationMs": 34,
            "resultSummary": "2 chunk(s) matched",
        },
    )
    assert resp.status_code == 200
    updated = resp.json()["data"]
    assert updated["id"] == "call-fixed"
    assert updated["status"] == "success"
    assert updated["durationMs"] == 34
    assert updated["resultSummary"] == "2 chunk(s) matched"

    calls = client.get("/api/v1/mcp/tool-calls").json()["data"]
    assert len(calls) == 1


def test_mcp_tool_call_redaction():
    client = _client()
    resp = client.post(
        "/api/v1/mcp/tool-calls",
        json={
            "tool": "secret_tool",
            "arguments": {
                "api_key": "abcdefghijklmnop123456",
                "query": "ok",
                "nested": {"Authorization": "Bearer abcdef"},
            },
            "resultSummary": "executed with Bearer abcdefghijklmnop and api_key: abcdefghijklmnop123456",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["arguments"]["api_key"] == "[REDACTED]"
    assert data["arguments"]["query"] == "ok"
    assert data["arguments"]["nested"]["Authorization"] == "[REDACTED]"
    summary = data["resultSummary"]
    assert "bearer [REDACTED]" in summary
    assert "[REDACTED]" in summary


def test_mcp_rerun_unknown_call_returns_404():
    client = _client()
    resp = client.post("/api/v1/mcp/tool-calls/nope/rerun")
    assert resp.status_code == 404


def test_mcp_rerun_without_executor_returns_400():
    client = _client()
    client.post("/api/v1/mcp/tool-calls", json={"id": "call-1", "tool": "unknown_tool"})
    resp = client.post("/api/v1/mcp/tool-calls/call-1/rerun")
    assert resp.status_code == 400
    assert "unknown_tool" in resp.json()["detail"]


def test_mcp_rerun_success_records_new_call(monkeypatch):
    monkeypatch.setitem(
        mcp_module.RERUN_EXECUTORS,
        "echo_tool",
        lambda args: f"echo {args.get('q')}",
    )
    client = _client()
    client.post(
        "/api/v1/mcp/tool-calls",
        json={"id": "call-echo", "tool": "echo_tool", "arguments": {"q": "hola"}},
    )

    resp = client.post("/api/v1/mcp/tool-calls/call-echo/rerun")
    assert resp.status_code == 200
    rerun = resp.json()["data"]
    assert rerun["rerunOf"] == "call-echo"
    assert rerun["status"] == "success"
    assert rerun["resultSummary"] == "echo hola"
    assert rerun["durationMs"] is not None

    calls = client.get("/api/v1/mcp/tool-calls").json()["data"]
    assert len(calls) == 2
    assert calls[0]["id"] != "call-echo"


def test_mcp_rerun_executor_error_is_recorded(monkeypatch):
    def _boom(_args):
        raise RuntimeError("executor exploded")

    monkeypatch.setitem(mcp_module.RERUN_EXECUTORS, "boom_tool", _boom)
    client = _client()
    client.post("/api/v1/mcp/tool-calls", json={"id": "call-boom", "tool": "boom_tool"})

    resp = client.post("/api/v1/mcp/tool-calls/call-boom/rerun")
    assert resp.status_code == 200
    rerun = resp.json()["data"]
    assert rerun["status"] == "error"
    assert "executor exploded" in rerun["error"]
    assert rerun["rerunOf"] == "call-boom"
    assert rerun["resultSummary"] is None


async def test_mcp_stream_sends_snapshot():
    from types import SimpleNamespace

    from starlette.requests import Request

    hub = MCPRegistry()
    hub.record_call({"tool": "rag_search", "arguments": {"query": "hola"}})
    app = SimpleNamespace(state=SimpleNamespace(mcp_registry=hub))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/mcp/tool-calls/stream",
        "headers": [],
        "query_string": b"",
        "app": app,
        "receive": None,
        "send": None,
    }
    resp = await mcp_module.stream_tool_calls(Request(scope))
    assert resp.media_type == "text/event-stream"
    text = ""
    async for chunk in resp.body_iterator:
        text += chunk
        if "event: tool_calls" in text:
            break
    assert "event: connected" in text
    assert "event: tool_calls" in text
    assert "rag_search" in text
    assert "hola" in text
    await resp.body_iterator.aclose()
    assert len(hub._subs) == 0


def test_registry_subscribe_and_publish():
    hub = MCPRegistry()
    queue, snapshot = hub.subscribe_calls()
    assert snapshot == []
    hub.record_call({"tool": "t1"})
    item = queue.get_nowait()
    assert item["event"] == "tool_call"
    assert item["data"]["tool"] == "t1"
    hub.unsubscribe_calls(queue)
    assert len(hub._subs) == 0


def test_registry_tool_calls_capped_at_500():
    hub = MCPRegistry()
    for index in range(501):
        hub.record_call({"tool": "t", "arguments": {"i": index}})
    assert len(hub._calls) == 500
    assert hub._calls[0]["arguments"]["i"] == 1
