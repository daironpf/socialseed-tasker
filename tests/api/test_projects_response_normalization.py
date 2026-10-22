"""Issue #587: project endpoints must answer 200 for real-world Project nodes.

The seed node arrives from Neo4j with ``slug = None`` and ``createdAt`` as a
``neo4j.time.DateTime`` driver object; ``ProjectResponse`` requires a string
slug and dates Pydantic accepts, so one bad node turned the whole listing into
a 400 VALIDATION_ERROR. The router now normalizes through a single mapper
(slug fallback from the name, driver dates to ISO) and skips malformed nodes
instead of sinking the listing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neo4j.time import DateTime

from socialseed_tasker.infrastructure.web_api.app import create_app

_REAL_NODE: dict[str, Any] = {
    "id": "socialseed",
    "name": "Social Seed",
    "slug": None,
    "description": None,
    "createdAt": DateTime.from_native(datetime(2026, 10, 13, 15, 57, 9, 504000, tzinfo=timezone.utc)),
    "updatedAt": DateTime.from_native(datetime(2026, 10, 13, 15, 57, 9, 504000, tzinfo=timezone.utc)),
}


class _Result:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    def single(self) -> dict[str, Any] | None:
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


class _Session:
    def __init__(self, nodes: list[Any]) -> None:
        self._nodes = nodes

    def run(self, query: str, *args: Any, **kwargs: Any) -> _Result:
        return _Result([{"p": node} for node in self._nodes])

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _Driver:
    def __init__(self, nodes: list[Any]) -> None:
        self._nodes = nodes

    def session(self, database: str | None = None) -> _Session:
        return _Session(self._nodes)


def _client(nodes: list[Any]) -> TestClient:
    app = create_app(repository=None, neo4j_driver=_Driver(nodes))
    return TestClient(app)


def test_projects_all_returns_200_even_without_slug() -> None:
    resp = _client([_REAL_NODE]).get("/api/v1/projects/all")
    assert resp.status_code == 200, resp.text[:400]
    body = resp.json()
    assert body["error"] is None
    assert len(body["data"]) == 1
    project = body["data"][0]
    assert project["slug"] == "social-seed"
    assert isinstance(project["createdAt"], str)
    assert "2026-10-13" in project["createdAt"]


def test_projects_current_serializes_driver_datetime() -> None:
    resp = _client([_REAL_NODE]).get("/api/v1/projects/current")
    assert resp.status_code == 200, resp.text[:400]
    body = resp.json()
    assert body["error"] is None
    project = body["data"]
    assert project["slug"] == "social-seed"
    assert isinstance(project["createdAt"], str)
    assert project["description"] == ""


def test_project_by_id_normalizes_response() -> None:
    resp = _client([_REAL_NODE]).get("/api/v1/projects/socialseed")
    assert resp.status_code == 200, resp.text[:400]
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["slug"] == "social-seed"
    assert isinstance(body["data"]["updatedAt"], str)


def test_projects_all_skips_malformed_node_without_sinking_listing() -> None:
    resp = _client(["corrupt-node", _REAL_NODE]).get("/api/v1/projects/all")
    assert resp.status_code == 200, resp.text[:400]
    body = resp.json()
    assert body["error"] is None
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == "socialseed"


def test_iso_timestamp_passthrough_helpers() -> None:
    from socialseed_tasker.infrastructure.web_api.routers.project import (
        _iso_timestamp,
        _slugify_project_name,
    )

    assert _iso_timestamp(None) is None
    assert _iso_timestamp("2026-01-02T03:04:05Z") == "2026-01-02T03:04:05Z"
    assert _iso_timestamp(_REAL_NODE["createdAt"]).startswith("2026-10-13")
    assert _slugify_project_name("  My Great Project ") == "my-great-project"
