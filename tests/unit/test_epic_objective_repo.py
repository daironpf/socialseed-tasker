"""Regression tests for Epic/Objective Neo4j persistence (issue #578).

``POST /api/v1/epics`` and ``POST /api/v1/objectives`` returned 500 because the
mixin read camelCase attributes (``epic.createdAt``) that do not exist on the
Pydantic entities (``created_at``). These tests pin the Cypher params written
to Neo4j and a create->read roundtrip through the repository.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from socialseed_tasker.domain.entities import Epic, Objective
from socialseed_tasker.infrastructure.neo4j_repository import Neo4jTaskRepository


class _EmptyResult:
    def single(self) -> None:
        return None

    def __iter__(self):
        return iter(())


class _FakeResult:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    def single(self) -> dict[str, Any] | None:
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


class _RecordingSession:
    def __init__(self, driver: _RecordingDriver) -> None:
        self._driver = driver

    def run(self, query: str, **params: Any) -> _EmptyResult | _FakeResult:
        self._driver.calls.append((query, params))
        return self._driver.next_result or _EmptyResult()

    def close(self) -> None:
        pass

    def __enter__(self) -> _RecordingSession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _RecordingDriver:
    """Minimal driver stub that records every session.run call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.next_result: _FakeResult | None = None

    @property
    def driver(self) -> _RecordingDriver:
        return self

    @property
    def database(self) -> str:
        return "neo4j"

    @contextmanager
    def session(self, database: str | None = None):
        yield _RecordingSession(self)


def _repo() -> tuple[Neo4jTaskRepository, _RecordingDriver]:
    driver = _RecordingDriver()
    return Neo4jTaskRepository(driver), driver


def test_create_epic_sends_iso_created_at_and_updated_at() -> None:
    repo, driver = _repo()
    epic = Epic(name="Epic A", description="desc")

    repo.create_epic(epic)

    query, params = driver.calls[0]
    assert "createdAt: $createdAt" in query
    assert "updatedAt: $updatedAt" in query
    assert params["createdAt"] == epic.created_at.isoformat()
    assert params["updatedAt"] == epic.updated_at.isoformat()
    assert params["name"] == "Epic A"
    assert params["status"] == "OPEN"


def test_create_objective_sends_iso_created_at_and_updated_at() -> None:
    repo, driver = _repo()
    objective = Objective(name="Obj A", quarter="2026Q4")

    repo.create_objective(objective)

    query, params = driver.calls[0]
    assert "createdAt: $createdAt" in query
    assert "updatedAt: $updatedAt" in query
    assert params["createdAt"] == objective.created_at.isoformat()
    assert params["updatedAt"] == objective.updated_at.isoformat()
    assert params["quarter"] == "2026Q4"
    assert params["status"] == "OPEN"


def test_get_epic_roundtrip_after_create() -> None:
    repo, driver = _repo()
    epic = Epic(name="Roundtrip", description="via node")
    repo.create_epic(epic)

    _, params = driver.calls[0]
    driver.next_result = _FakeResult(
        [
            {
                "e": {
                    "id": params["id"],
                    "name": params["name"],
                    "description": params["description"],
                    "objective_id": None,
                    "status": params["status"],
                    "createdAt": params["createdAt"],
                    "updatedAt": params["updatedAt"],
                }
            }
        ]
    )

    fetched = repo.get_epic(params["id"])

    assert fetched is not None
    assert fetched.id == epic.id
    assert fetched.name == "Roundtrip"
    assert fetched.status.value == "OPEN"


def test_get_objective_roundtrip_after_create() -> None:
    repo, driver = _repo()
    objective = Objective(name="Obj Round", quarter="2026Q1")
    repo.create_objective(objective)

    _, params = driver.calls[0]
    driver.next_result = _FakeResult(
        [
            {
                "o": {
                    "id": params["id"],
                    "name": params["name"],
                    "description": params["description"],
                    "status": params["status"],
                    "quarter": params["quarter"],
                    "createdAt": params["createdAt"],
                    "updatedAt": params["updatedAt"],
                }
            }
        ]
    )

    fetched = repo.get_objective(params["id"])

    assert fetched is not None
    assert fetched.id == objective.id
    assert fetched.quarter == "2026Q1"
    assert fetched.status.value == "OPEN"


def test_list_epics_and_objectives_do_not_crash_on_empty() -> None:
    repo, _ = _repo()
    assert repo.list_epics() == []
    assert repo.list_objectives() == []


# ---------------------------------------------------------------------------
# update_epic / update_objective (issue #579): empty SET, updatedAt, key safety
# ---------------------------------------------------------------------------


def test_update_epic_with_empty_updates_runs_no_query() -> None:
    repo, driver = _repo()

    repo.update_epic("epic-1", {})

    assert driver.calls == []


def test_update_epic_sets_fields_and_renews_updated_at() -> None:
    repo, driver = _repo()

    repo.update_epic("epic-1", {"name": "New name", "status": "IN_PROGRESS"})

    assert len(driver.calls) == 1
    query, params = driver.calls[0]
    assert "SET" in query
    assert "e.updatedAt = $updatedAt" in query
    assert "e.name = $name" in query
    assert "e.status = $status" in query
    assert params["id"] == "epic-1"
    assert params["name"] == "New name"
    assert params["status"] == "IN_PROGRESS"
    assert params["updatedAt"].endswith("+00:00")


def test_update_epic_drops_protected_and_unknown_keys() -> None:
    repo, driver = _repo()

    repo.update_epic(
        "epic-1",
        {"name": "ok", "id": "evil", "createdAt": "evil", "status = 'x": "evil", "foo": 1},
    )

    assert len(driver.calls) == 1
    query, params = driver.calls[0]
    assert "e.name = $name" in query
    assert "e.id" not in query
    assert "e.createdAt" not in query
    assert "foo" not in query
    assert params["id"] == "epic-1"
    assert "createdAt" not in params
    assert "foo" not in params


def test_update_epic_with_only_invalid_keys_runs_no_query() -> None:
    repo, driver = _repo()

    repo.update_epic("epic-1", {"id": "evil", "createdAt": "evil"})

    assert driver.calls == []


def test_update_objective_with_empty_updates_runs_no_query() -> None:
    repo, driver = _repo()

    repo.update_objective("obj-1", {})

    assert driver.calls == []


def test_update_objective_sets_fields_and_renews_updated_at() -> None:
    repo, driver = _repo()

    repo.update_objective("obj-1", {"quarter": "2026Q2", "status": "COMPLETED"})

    assert len(driver.calls) == 1
    query, params = driver.calls[0]
    assert "SET" in query
    assert "o.updatedAt = $updatedAt" in query
    assert "o.quarter = $quarter" in query
    assert "o.status = $status" in query
    assert params["id"] == "obj-1"
    assert params["quarter"] == "2026Q2"
    assert params["status"] == "COMPLETED"
    assert params["updatedAt"].endswith("+00:00")


def test_update_objective_drops_protected_and_unknown_keys() -> None:
    repo, driver = _repo()

    repo.update_objective("obj-1", {"name": "ok", "id": "evil", "objective_id": "evil", "foo": 1})

    assert len(driver.calls) == 1
    query, params = driver.calls[0]
    assert "o.name = $name" in query
    assert "o.id" not in query
    assert "foo" not in query
    assert params["id"] == "obj-1"
    assert "foo" not in params


def test_update_objective_with_only_invalid_keys_runs_no_query() -> None:
    repo, driver = _repo()

    repo.update_objective("obj-1", {"id": "evil", "foo": 1})

    assert driver.calls == []
