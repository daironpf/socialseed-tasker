"""Issue #585: smoke over the 10 endpoints that returned 500 ``ParameterMissing``.

A validating fake driver emulates Neo4j's ``Expected parameter(s): X`` behaviour:
every ``session.run(query, ...)`` must receive all ``$param`` tokens of the
query. Any endpoint that misses one raises inside the app and lands on 500,
failing the test. Ids do not exist, so legal outcomes are 200/404 — never 500.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.domain.entities import Issue
from socialseed_tasker.infrastructure.neo4j_repository import Neo4jTaskRepository
from socialseed_tasker.infrastructure.web_api.app import create_app

ISSUE_ID = "00000000-0585-4000-8000-000000000585"
MISSING = "missing-585"


def _cypher_params(query: str) -> set[str]:
    return set(re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)", query))


class _FakeResult:
    def __init__(self, records: list[dict[str, Any]] | None = None) -> None:
        self._records = records or []

    def single(self) -> dict[str, Any] | None:
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


class _ValidatingSession:
    def __init__(self, driver: _ValidatingDriver) -> None:
        self._driver = driver

    def run(self, query: str, *args: Any, **kwargs: Any) -> _FakeResult:
        params: dict[str, Any] = {}
        for arg in args:
            if isinstance(arg, dict):
                params.update(arg)
        params.update(kwargs)
        missing = sorted(_cypher_params(query) - set(params))
        if missing:
            self._driver.errors.append((query.splitlines()[0][:60], missing))
            raise Exception(f"Expected parameter(s): {', '.join(missing)}")
        self._driver.calls.append((query, params))
        return _FakeResult()

    def __enter__(self) -> _ValidatingSession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _ValidatingDriver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.errors: list[tuple[str, list[str]]] = []
        self.database = "neo4j"
        self.driver = self  # wrapper-style access used by _session()/routers

    def session(self, database: str | None = None) -> _ValidatingSession:
        return _ValidatingSession(self)


class _AffectsRepository:
    """Real Neo4j issue repository for AFFECTS, with an in-memory get_issue."""

    def __init__(self, driver: _ValidatingDriver) -> None:
        self._neo4j = Neo4jTaskRepository(driver)
        self._issue = Issue(title="smoke", component_id=uuid4())

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._issue if issue_id == ISSUE_ID else None

    def add_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        self._neo4j.add_affects_symbol(issue_id, symbol_id)

    def remove_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        self._neo4j.remove_affects_symbol(issue_id, symbol_id)

    def get_affected_symbols(self, issue_id: str) -> list[dict[str, Any]]:
        return self._neo4j.get_affected_symbols(issue_id)


@pytest.fixture()
def smoke_env(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, _ValidatingDriver]:
    driver = _ValidatingDriver()
    app = create_app(repository=_AffectsRepository(driver), neo4j_driver=driver)
    monkeypatch.setattr(
        "socialseed_tasker.application.wiring.get_driver",
        lambda: driver,
        raising=True,
    )
    return TestClient(app), driver


def _assert_ok(resp: Any, driver: _ValidatingDriver, label: str) -> None:
    assert resp.status_code != 500, f"{label}: 500 -> {resp.text[:400]}"
    assert driver.errors == [], f"{label}: ParameterMissing {driver.errors}"
    assert resp.status_code in (200, 201, 204, 404), f"{label}: {resp.status_code} {resp.text[:200]}"


def test_get_policies_endpoints(smoke_env: tuple[TestClient, _ValidatingDriver]) -> None:
    client, driver = smoke_env
    for path in (
        f"/api/v1/policies/project/{MISSING}",
        f"/api/v1/policies/agent/{MISSING}",
        f"/api/v1/policies/component/{MISSING}",
    ):
        _assert_ok(client.get(path), driver, f"GET {path}")


def test_link_policy_endpoints(smoke_env: tuple[TestClient, _ValidatingDriver]) -> None:
    client, driver = smoke_env
    for path in (
        f"/api/v1/policies/{MISSING}/link/agent/{MISSING}",
        f"/api/v1/policies/{MISSING}/link/component/{MISSING}",
    ):
        _assert_ok(client.post(path), driver, f"POST {path}")


def test_agent_specialists_endpoints(smoke_env: tuple[TestClient, _ValidatingDriver]) -> None:
    client, driver = smoke_env
    _assert_ok(client.get(f"/api/v1/agents/{MISSING}/specialists"), driver, "GET specialists")
    _assert_ok(
        client.post(f"/api/v1/agents/{MISSING}/specialists/{MISSING}"), driver, "POST specialist"
    )
    _assert_ok(
        client.delete(f"/api/v1/agents/{MISSING}/specialists/{MISSING}"),
        driver,
        "DELETE specialist",
    )


def test_component_specialists_endpoint(smoke_env: tuple[TestClient, _ValidatingDriver]) -> None:
    client, driver = smoke_env
    _assert_ok(
        client.get(f"/api/v1/components/{MISSING}/specialists"), driver, "GET component specialists"
    )


def test_project_agents_endpoints(smoke_env: tuple[TestClient, _ValidatingDriver]) -> None:
    client, driver = smoke_env
    _assert_ok(client.get(f"/api/v1/projects/{MISSING}/agents"), driver, "GET project agents")
    _assert_ok(
        client.post(f"/api/v1/projects/{MISSING}/agents/{MISSING}"), driver, "POST assign"
    )
    _assert_ok(
        client.delete(f"/api/v1/projects/{MISSING}/agents/{MISSING}"), driver, "DELETE unassign"
    )


def test_link_commit_agent_endpoint(smoke_env: tuple[TestClient, _ValidatingDriver]) -> None:
    client, driver = smoke_env
    _assert_ok(
        client.post(f"/api/v1/commits/{'a' * 40}/link/agent/{MISSING}"),
        driver,
        "POST link commit agent",
    )


def test_issue_affects_endpoints_with_real_issue(
    smoke_env: tuple[TestClient, _ValidatingDriver],
) -> None:
    client, driver = smoke_env
    path = f"/api/v1/issues/{ISSUE_ID}/affects"
    _assert_ok(client.post(path, json="sym-585"), driver, "POST affects")
    _assert_ok(client.get(path), driver, "GET affects")
    resp = client.request(
        "DELETE", path, content='"sym-585"', headers={"Content-Type": "application/json"}
    )
    _assert_ok(resp, driver, "DELETE affects")
    assert driver.calls, "no Cypher reached Neo4j for the affects flow"


def test_issue_affects_unknown_issue_is_404(
    smoke_env: tuple[TestClient, _ValidatingDriver],
) -> None:
    client, driver = smoke_env
    resp = client.post(f"/api/v1/issues/{MISSING}/affects", json="sym-585")
    _assert_ok(resp, driver, "POST affects unknown")
    assert resp.status_code == 404
