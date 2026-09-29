"""MCP registry and live tool-call inspector API (issue #524).

Endpoints consumed by the MCP Inspector view:

- ``GET    /mcp/servers``                     registered MCP servers
- ``POST   /mcp/servers``                     register / update a server
- ``GET    /mcp/sessions``                    active MCP client sessions
- ``POST   /mcp/sessions``                    register / heartbeat a session
- ``DELETE /mcp/sessions/{id}``               disconnect a session
- ``GET    /mcp/tool-calls``                  tool-call history (filters)
- ``POST   /mcp/tool-calls``                  record / update a tool call
- ``GET    /mcp/tool-calls/stream``           SSE stream (snapshot + live)
- ``POST   /mcp/tool-calls/{id}/rerun``       re-execute a recorded call

State lives in an in-process :class:`MCPRegistry` stored on
``app.state.mcp_registry`` (same pattern as the realtime hub). Argument
payloads are redacted server-side before storage and re-execution runs
through the registered tool executors.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import deque
from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from socialseed_tasker.infrastructure.embedding_service import SecretFilter
from socialseed_tasker.infrastructure.web_api.schemas import APIResponse

mcp_router = APIRouter(tags=["mcp"])

_HEARTBEAT_SECONDS = 15.0
_MAX_TOOL_CALLS = 500
_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "access_token",
        "refresh_token",
        "secret",
        "secret_key",
        "password",
        "token",
    }
)

RerunExecutor = Callable[[dict[str, Any]], str]


def _sse(event: str, data: Any) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _redact(value: Any) -> Any:
    """Recursively replace secret-looking dict values with ``[REDACTED]``."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            redacted[key] = "[REDACTED]" if normalized in _SECRET_KEYS else _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class CamelModel(BaseModel):
    """Request/response model serialised to camelCase (frontend contract)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ServerRegisterRequest(CamelModel):
    id: str | None = None
    name: str = Field(..., min_length=1)
    transport: str = "http"
    url: str | None = None
    tools: list[str] = Field(default_factory=list)
    status: str = "online"


class SessionUpsertRequest(CamelModel):
    id: str | None = None
    client_name: str = Field(..., min_length=1)
    client_type: str = "custom"
    status: str = "active"
    project_id: str | None = None
    user_id: str | None = None
    server: str | None = None
    context_consumed: int = 0
    context_limit: int = 524288
    cypher_queries: int = 0
    cypher_queries_per_min: float = 0.0
    tools_used: list[str] = Field(default_factory=list)


class ToolCallRecordRequest(CamelModel):
    id: str | None = None
    session_id: str | None = None
    server: str | None = None
    tool: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: str = "running"
    duration_ms: int | None = None
    result_summary: str | None = None
    error: str | None = None
    rerun_of: str | None = None


class ServerResponse(CamelModel):
    id: str
    name: str
    transport: str
    url: str | None = None
    tools: list[str]
    status: str
    last_seen: str


class SessionResponse(CamelModel):
    id: str
    client_name: str
    client_type: str
    status: str
    connected_at: str
    last_activity_at: str
    uptime: int
    context_consumed: int
    context_limit: int
    cypher_queries: int
    cypher_queries_per_min: float
    tools_used: list[str]
    project_id: str | None = None
    user_id: str | None = None
    server: str | None = None


class ToolCallResponse(CamelModel):
    id: str
    session_id: str | None
    server: str | None
    tool: str
    arguments: dict[str, Any]
    status: str
    started_at: str
    duration_ms: int | None
    result_summary: str | None
    error: str | None
    rerun_of: str | None


def _session_wire(record: dict[str, Any]) -> dict[str, Any]:
    """Project an internal session record onto the camelCase wire shape."""
    connected_ts = float(record.get("connectedTs", time.time()))
    return {
        "id": record["id"],
        "clientName": record["clientName"],
        "clientType": record["clientType"],
        "status": record["status"],
        "connectedAt": record["connectedAt"],
        "lastActivityAt": record["lastActivityAt"],
        "uptime": max(0, int(time.time() - connected_ts)),
        "contextConsumed": record["contextConsumed"],
        "contextLimit": record["contextLimit"],
        "cypherQueries": record["cypherQueries"],
        "cypherQueriesPerMin": record["cypherQueriesPerMin"],
        "toolsUsed": record["toolsUsed"],
        "projectId": record.get("projectId"),
        "userId": record.get("userId"),
        "server": record.get("server"),
    }


class MCPRegistry:
    """In-process registry of MCP servers, sessions and tool calls.

    All methods are synchronous and run on the event loop, so a
    ``record_call`` call is atomic with respect to SSE subscribers.
    """

    def __init__(self) -> None:
        self._servers: dict[str, dict[str, Any]] = {}
        self._sessions: dict[str, dict[str, Any]] = {}
        self._calls: deque[dict[str, Any]] = deque(maxlen=_MAX_TOOL_CALLS)
        self._subs: list[asyncio.Queue[dict[str, Any]]] = []

    # ------------------------------------------------------------- publish

    def publish(self, event: str, data: Any) -> None:
        payload = {"event": event, "data": data}
        for queue in self._subs:
            queue.put_nowait(payload)

    def subscribe_calls(self) -> tuple[asyncio.Queue[dict[str, Any]], list[dict[str, Any]]]:
        """Atomically snapshot recent calls and register a live subscriber."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        snapshot = self.calls(limit=50)
        self._subs.append(queue)
        return queue, snapshot

    def unsubscribe_calls(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        if queue in self._subs:
            self._subs.remove(queue)

    # ------------------------------------------------------------- servers

    def register_server(self, payload: dict[str, Any]) -> dict[str, Any]:
        server_id = str(payload.get("id") or f"srv-{uuid.uuid4().hex[:8]}")
        existing = self._servers.get(server_id, {})
        now = _now_iso()
        record: dict[str, Any] = {
            "id": server_id,
            "name": str(payload.get("name") or server_id),
            "transport": str(payload.get("transport") or "http"),
            "url": payload.get("url"),
            "tools": list(payload.get("tools") or []),
            "status": str(payload.get("status") or "online"),
            "registeredAt": existing.get("registeredAt", now),
            "lastSeen": now,
        }
        self._servers[server_id] = record
        self.publish("server_update", record)
        return record

    def servers(self) -> list[dict[str, Any]]:
        return sorted(self._servers.values(), key=lambda s: str(s.get("name", "")))

    # ------------------------------------------------------------ sessions

    def upsert_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = str(payload.get("id") or f"sess-{uuid.uuid4().hex[:8]}")
        existing = self._sessions.get(session_id)
        now = _now_iso()

        def pick(field: str, default: Any) -> Any:
            value = payload.get(field)
            if value is not None:
                return value
            if existing is not None:
                return existing.get(field, default)
            return default

        record: dict[str, Any] = {
            "id": session_id,
            "clientName": str(pick("clientName", session_id)),
            "clientType": str(pick("clientType", "custom")),
            "status": str(pick("status", "active")),
            "connectedAt": existing["connectedAt"] if existing else now,
            "connectedTs": existing["connectedTs"] if existing else time.time(),
            "lastActivityAt": now,
            "contextConsumed": int(pick("contextConsumed", 0)),
            "contextLimit": int(pick("contextLimit", 524288)),
            "cypherQueries": int(pick("cypherQueries", 0)),
            "cypherQueriesPerMin": float(pick("cypherQueriesPerMin", 0.0)),
            "toolsUsed": list(pick("toolsUsed", []) or []),
            "projectId": pick("projectId", None),
            "userId": pick("userId", None),
            "server": pick("server", None),
        }
        self._sessions[session_id] = record
        self.publish("session_update", _session_wire(record))
        return record

    def remove_session(self, session_id: str) -> dict[str, Any] | None:
        record = self._sessions.pop(session_id, None)
        if record is not None:
            self.publish("session_removed", {"id": session_id})
        return record

    def sessions(self) -> list[dict[str, Any]]:
        return [_session_wire(record) for record in self._sessions.values()]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        record = self._sessions.get(session_id)
        return _session_wire(record) if record else None

    # ---------------------------------------------------------- tool calls

    def record_call(self, payload: dict[str, Any]) -> dict[str, Any]:
        arguments = _redact(payload.get("arguments") or {})
        result_summary = payload.get("resultSummary")
        if isinstance(result_summary, str):
            result_summary = SecretFilter.filter(result_summary)
        error = payload.get("error")
        if isinstance(error, str):
            error = SecretFilter.filter(error)

        call_id = payload.get("id")
        if call_id is not None:
            call_id = str(call_id)
            for existing in self._calls:
                if existing["id"] == call_id:
                    if payload.get("status") is not None:
                        existing["status"] = str(payload["status"])
                    if payload.get("durationMs") is not None:
                        existing["durationMs"] = int(payload["durationMs"])
                    if result_summary is not None:
                        existing["resultSummary"] = result_summary
                    if error is not None:
                        existing["error"] = error
                    if payload.get("arguments"):
                        existing["arguments"] = arguments
                    self.publish("tool_call_update", dict(existing))
                    return dict(existing)

        record: dict[str, Any] = {
            "id": call_id or f"call-{uuid.uuid4().hex[:8]}",
            "sessionId": payload.get("sessionId"),
            "server": payload.get("server"),
            "tool": str(payload["tool"]),
            "arguments": arguments,
            "status": str(payload.get("status") or "running"),
            "startedAt": _now_iso(),
            "durationMs": payload.get("durationMs"),
            "resultSummary": result_summary,
            "error": error,
            "rerunOf": payload.get("rerunOf"),
        }
        self._calls.append(record)
        self.publish("tool_call", dict(record))
        return dict(record)

    def get_call(self, call_id: str) -> dict[str, Any] | None:
        for call in self._calls:
            if call["id"] == call_id:
                return dict(call)
        return None

    def calls(
        self,
        *,
        limit: int = 50,
        session_id: str | None = None,
        server: str | None = None,
        tool: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        filtered = [
            dict(call)
            for call in self._calls
            if (session_id is None or call.get("sessionId") == session_id)
            and (server is None or call.get("server") == server)
            and (tool is None or call.get("tool") == tool)
            and (status is None or call.get("status") == status)
        ]
        filtered.reverse()
        return filtered[:limit]


def _registry(request: Request) -> MCPRegistry:
    hub: MCPRegistry | None = getattr(request.app.state, "mcp_registry", None)
    if hub is None:
        hub = MCPRegistry()
        request.app.state.mcp_registry = hub
    return hub


# ------------------------------------------------------------ rerun tools


def _exec_rag_search(args: dict[str, Any]) -> str:
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("rag_search requires a non-empty 'query' argument")
    limit = int(args.get("limit", 5))
    threshold = float(args.get("threshold", 0.0))
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

    driver = get_driver()
    if driver is None:
        raise RuntimeError("Neo4j not connected")
    repo = RAGRepository(driver)
    results = repo.search(query=query, limit=limit, threshold=threshold)
    return f"{len(results)} chunk(s) matched"


def _exec_rag_stats(_args: dict[str, Any]) -> str:
    from socialseed_tasker.application.wiring import get_driver
    from socialseed_tasker.infrastructure.neo4j_rag_repository import RAGRepository

    driver = get_driver()
    if driver is None:
        raise RuntimeError("Neo4j not connected")
    repo = RAGRepository(driver)
    stats = repo.get_stats()
    total = stats.get("total", 0)
    return f"{total} embeddings indexed"


RERUN_EXECUTORS: dict[str, RerunExecutor] = {
    "rag_search": _exec_rag_search,
    "rag_stats": _exec_rag_stats,
}


# --------------------------------------------------------------- servers


@mcp_router.get("/mcp/servers")
async def list_servers(request: Request) -> APIResponse[list[ServerResponse]]:
    items = [ServerResponse(**s) for s in _registry(request).servers()]
    return APIResponse[list[ServerResponse]](data=items)


@mcp_router.post("/mcp/servers")
async def register_server(body: ServerRegisterRequest, request: Request) -> APIResponse[ServerResponse]:
    record = _registry(request).register_server(body.model_dump(by_alias=True))
    return APIResponse[ServerResponse](data=ServerResponse(**record))


# -------------------------------------------------------------- sessions


@mcp_router.get("/mcp/sessions")
async def list_sessions(request: Request) -> APIResponse[list[SessionResponse]]:
    items = [SessionResponse(**s) for s in _registry(request).sessions()]
    return APIResponse[list[SessionResponse]](data=items)


@mcp_router.post("/mcp/sessions")
async def upsert_session(body: SessionUpsertRequest, request: Request) -> APIResponse[SessionResponse]:
    record = _registry(request).upsert_session(body.model_dump(by_alias=True))
    return APIResponse[SessionResponse](data=SessionResponse(**_session_wire(record)))


@mcp_router.delete("/mcp/sessions/{session_id}")
async def delete_session(session_id: str, request: Request) -> APIResponse[dict[str, str]]:
    removed = _registry(request).remove_session(session_id)
    if removed is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return APIResponse[dict[str, str]](data={"id": session_id})


# ------------------------------------------------------------ tool calls


@mcp_router.get("/mcp/tool-calls")
async def list_tool_calls(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    session_id: str | None = None,
    server: str | None = None,
    tool: str | None = None,
    status: str | None = None,
) -> APIResponse[list[ToolCallResponse]]:
    calls = _registry(request).calls(
        limit=limit, session_id=session_id, server=server, tool=tool, status=status
    )
    return APIResponse[list[ToolCallResponse]](data=[ToolCallResponse(**c) for c in calls])


@mcp_router.post("/mcp/tool-calls")
async def record_tool_call(body: ToolCallRecordRequest, request: Request) -> APIResponse[ToolCallResponse]:
    record = _registry(request).record_call(body.model_dump(by_alias=True))
    return APIResponse[ToolCallResponse](data=ToolCallResponse(**record))


@mcp_router.get("/mcp/tool-calls/stream")
async def stream_tool_calls(request: Request) -> StreamingResponse:
    """Live stream of MCP tool calls: initial snapshot, then every update."""
    hub = _registry(request)
    queue, snapshot = hub.subscribe_calls()

    async def generate() -> AsyncGenerator[str, None]:
        try:
            yield _sse("connected", {"replayed": len(snapshot)})
            yield _sse("tool_calls", {"calls": snapshot})
            while True:
                if await request.is_disconnected():
                    return
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    yield _sse("ping", {"ts": int(time.time() * 1000)})
                    continue
                yield _sse(item["event"], item["data"])
        finally:
            hub.unsubscribe_calls(queue)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


@mcp_router.post("/mcp/tool-calls/{call_id}/rerun")
async def rerun_tool_call(call_id: str, request: Request) -> APIResponse[ToolCallResponse]:
    """Re-execute a recorded tool call through its registered executor."""
    hub = _registry(request)
    original = hub.get_call(call_id)
    if original is None:
        raise HTTPException(status_code=404, detail=f"Tool call {call_id} not found")
    executor = RERUN_EXECUTORS.get(str(original["tool"]))
    if executor is None:
        raise HTTPException(status_code=400, detail=f"No executor registered for tool '{original['tool']}'")

    started = time.perf_counter()
    try:
        summary = executor(original["arguments"])
        status = "success"
        error: str | None = None
    except Exception as exc:
        summary = None
        status = "error"
        error = str(exc)
    duration_ms = int((time.perf_counter() - started) * 1000)

    record = hub.record_call(
        {
            "sessionId": original.get("sessionId"),
            "server": original.get("server"),
            "tool": original["tool"],
            "arguments": original["arguments"],
            "status": status,
            "durationMs": duration_ms,
            "resultSummary": summary,
            "error": error,
            "rerunOf": call_id,
        }
    )
    return APIResponse[ToolCallResponse](data=ToolCallResponse(**record))
