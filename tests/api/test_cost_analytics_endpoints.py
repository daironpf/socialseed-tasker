"""Issue #580: the four ``/cost-*`` endpoints answer 200 with valid Cypher.

Each endpoint runs through the real ``CostAnalyticsRepositoryMixin`` against a
recording driver, so the test asserts both the API envelope (200, mapped data)
and the exact Cypher that reaches Neo4j (shared ``CASE tier`` rate expression,
no string-literal WHEN, no orphan ``hours``).
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.neo4j_impl.cost_mixin import (
    CostAnalyticsRepositoryMixin,
)
from socialseed_tasker.infrastructure.web_api.app import create_app

COST_PATHS = [
    "/api/v1/cost-per-component",
    "/api/v1/cost-per-epic",
    "/api/v1/cost-per-project",
    "/api/v1/cost-summary",
]

_RECORD: dict[str, Any] = {
    "componentId": "comp-1",
    "component_name": "Backend",
    "epicId": "epic-1",
    "epic_name": "MVP",
    "projectId": "proj-1",
    "project_name": "SocialSeed",
    "actual_cost": 750.0,
    "avg_hourly_rate": 75.0,
    "total_hours": 10.0,
    "issue_count": 3,
    "total_actual_cost": 750.0,
    "total_issues_closed": 3,
}


class _Result:
    def single(self) -> dict[str, Any] | None:
        return _RECORD

    def __iter__(self):
        return iter([_RECORD])


class _Session:
    def __init__(self, sink: list[str]) -> None:
        self._sink = sink

    def run(self, query: str, *args: Any, **kwargs: Any) -> _Result:
        self._sink.append(query)
        return _Result()

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _Driver:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def session(self, database: str | None = None) -> _Session:
        return _Session(self.queries)


class _CostRepository(CostAnalyticsRepositoryMixin):
    def __init__(self, driver: _Driver) -> None:
        self._driver = driver


def _client_with(driver: _Driver) -> TestClient:
    return TestClient(create_app(repository=_CostRepository(driver)))


@pytest.mark.parametrize("path", COST_PATHS)
def test_cost_endpoint_returns_200_with_mapped_data(path: str) -> None:
    resp = _client_with(_Driver()).get(path)
    assert resp.status_code == 200, resp.text[:300]
    body = resp.json()
    assert body["error"] is None
    assert body["data"] is not None


@pytest.mark.parametrize("path", COST_PATHS)
def test_cost_endpoint_sends_valid_cypher(path: str) -> None:
    driver = _Driver()
    _client_with(driver).get(path)
    assert len(driver.queries) == 1, driver.queries
    query = driver.queries[0]
    assert "CASE WHEN '" not in query, "string literal where Boolean expected (22NB1)"
    assert "CASE tier WHEN" in query, "shared simple CASE over the tier variable"
    assert "COLLECT(" not in query, "aggregation must not discard hours/tier scope"
    assert "AS hours" in query


def test_cost_summary_returns_typed_totals() -> None:
    resp = _client_with(_Driver()).get("/api/v1/cost-summary")
    assert resp.status_code == 200, resp.text[:300]
    data = resp.json()["data"]
    assert data == {
        "total_actual_cost": 750.0,
        "total_hours": 10.0,
        "total_issues_closed": 3,
    }


def test_cost_per_component_returns_full_row() -> None:
    resp = _client_with(_Driver()).get("/api/v1/cost-per-component")
    assert resp.status_code == 200, resp.text[:300]
    rows = resp.json()["data"]
    assert rows == [
        {
            "componentId": "comp-1",
            "component_name": "Backend",
            "actual_cost": 750.0,
            "avg_hourly_rate": 75.0,
            "total_hours": 10.0,
            "issue_count": 3,
        }
    ]
