"""Tests for issue assignee/created_by and the per-user issue endpoints (#569).

Covers: server-side ``created_by`` from the JWT sub, optional ``assignee`` on
create, assign/unassign on PATCH, ``GET /issues`` filters and the
``GET /users/{id}/issues`` + ``/issue-stats`` view semantics (assigned /
created / completed) with their 401/404/422 edges.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import user as user_router

_UNIT_DIR = Path(__file__).resolve().parents[1] / "unit"

UID_ANA = "uid-ana"
UID_BOT = "uid-bot"
UID_GHOST = "uid-ghost"


@pytest.fixture()
def repo():
    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    return MockRepository()


@pytest.fixture()
def app(repo):
    return create_app(repository=repo)


@pytest.fixture()
def client(app):
    return TestClient(app)


class _StubPgRepository:
    """Existence checks against a fixed set of PG uids (issue #569)."""

    def __init__(self, uids: set[str]) -> None:
        self._uids = set(uids)

    def get_user(self, user_id: str) -> dict | None:
        return {"id": user_id} if user_id in self._uids else None


@pytest.fixture()
def pg_users(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        user_router, "_pg_repository", lambda: _StubPgRepository({UID_ANA, UID_BOT})
    )


def _token(sub: str) -> str:
    return issue_tokens({"id": sub, "username": sub, "role": "VIEWER"})["access_token"]


def _auth(sub: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(sub)}"}


def _create_component(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/components",
        json={"name": "Backend", "project": "test-project"},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["data"]["id"]


def _create_issue(
    client: TestClient,
    title: str,
    component_id: str,
    headers: dict[str, str] | None = None,
    extra: dict | None = None,
) -> dict:
    payload = {"title": title, "component_id": component_id}
    payload.update(extra or {})
    resp = client.post("/api/v1/issues", json=payload, headers=headers or {})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


# ---------------------------------------------------------------------------
# POST /issues - created_by from the JWT sub, optional assignee (#569)
# ---------------------------------------------------------------------------


def test_create_issue_sets_created_by_from_jwt_sub(client: TestClient):
    component_id = _create_component(client)
    issue = _create_issue(
        client, "Created by JWT sub", component_id, headers=_auth(UID_ANA)
    )
    assert issue["created_by"] == UID_ANA
    assert issue["assignee"] is None


def test_create_issue_without_token_leaves_created_by_unset(client: TestClient):
    component_id = _create_component(client)
    issue = _create_issue(client, "Anonymous create", component_id)
    assert issue["created_by"] is None


def test_create_issue_with_assignee(client: TestClient):
    component_id = _create_component(client)
    issue = _create_issue(
        client,
        "Assigned on create",
        component_id,
        headers=_auth(UID_ANA),
        extra={"assignee": UID_BOT},
    )
    assert issue["assignee"] == UID_BOT
    assert issue["created_by"] == UID_ANA


def test_update_issue_assign_and_unassign(client: TestClient):
    component_id = _create_component(client)
    issue = _create_issue(client, "Assign roundtrip", component_id)

    assigned = client.patch(
        f"/api/v1/issues/{issue['id']}", json={"assignee": UID_BOT}
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["data"]["assignee"] == UID_BOT

    unassigned = client.patch(
        f"/api/v1/issues/{issue['id']}", json={"assignee": None}
    )
    assert unassigned.status_code == 200, unassigned.text
    assert unassigned.json()["data"]["assignee"] is None


# ---------------------------------------------------------------------------
# GET /issues - filters (#569)
# ---------------------------------------------------------------------------


def test_list_issues_filter_by_assignee(client: TestClient):
    component_id = _create_component(client)
    target = _create_issue(
        client, "Filter assignee target", component_id, extra={"assignee": UID_BOT}
    )
    _create_issue(client, "Filter assignee other", component_id)

    resp = client.get("/api/v1/issues", params={"assignee": UID_BOT})
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert [i["id"] for i in items] == [target["id"]]
    assert items[0]["assignee"] == UID_BOT


def test_list_issues_filter_by_created_by(client: TestClient):
    component_id = _create_component(client)
    ana_issue = _create_issue(
        client, "Created by ana", component_id, headers=_auth(UID_ANA)
    )
    _create_issue(client, "Created by bot", component_id, headers=_auth(UID_BOT))

    resp = client.get("/api/v1/issues", params={"created_by": UID_ANA})
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert [i["id"] for i in items] == [ana_issue["id"]]
    assert items[0]["created_by"] == UID_ANA


# ---------------------------------------------------------------------------
# GET /users/{id}/issues + /issue-stats (#569)
# ---------------------------------------------------------------------------


def _seed_view_issues(client: TestClient, component_id: str) -> dict[str, str]:
    """i1: bot/ana OPEN; i2: bot-created ana OPEN; i3: ana/ana CLOSED."""
    i1 = _create_issue(
        client,
        "view i1 assigned to ana",
        component_id,
        headers=_auth(UID_BOT),
        extra={"assignee": UID_ANA},
    )
    i2 = _create_issue(
        client,
        "view i2 created by ana",
        component_id,
        headers=_auth(UID_ANA),
        extra={"assignee": UID_BOT},
    )
    i3 = _create_issue(
        client,
        "view i3 completed by ana",
        component_id,
        headers=_auth(UID_ANA),
        extra={"assignee": UID_ANA},
    )
    closed = client.patch(f"/api/v1/issues/{i3['id']}", json={"status": "CLOSED"})
    assert closed.status_code == 200, closed.text
    return {"i1": i1["id"], "i2": i2["id"], "i3": i3["id"]}


def _get_kinds(client: TestClient, user_id: str, headers: dict[str, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for kind in ("assigned", "created", "completed"):
        resp = client.get(
            f"/api/v1/users/{user_id}/issues",
            params={"kind": kind},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        out[kind] = [i["id"] for i in resp.json()["data"]]
    return out


def test_user_issues_endpoint_kinds(client: TestClient, pg_users):
    component_id = _create_component(client)
    ids = _seed_view_issues(client, component_id)
    headers = _auth(UID_ANA)

    kinds = _get_kinds(client, UID_ANA, headers)
    assert kinds["assigned"] == [ids["i1"]]
    assert kinds["created"] == [ids["i2"]]
    assert kinds["completed"] == [ids["i3"]]

    kinds_bot = _get_kinds(client, UID_BOT, headers)
    assert kinds_bot["assigned"] == [ids["i2"]]
    assert kinds_bot["created"] == [ids["i1"]]
    assert kinds_bot["completed"] == []


def test_user_issue_stats_counts(client: TestClient, pg_users):
    component_id = _create_component(client)
    _seed_view_issues(client, component_id)

    resp = client.get(
        f"/api/v1/users/{UID_ANA}/issue-stats", headers=_auth(UID_ANA)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"assigned": 1, "created": 1, "completed": 1}


def test_user_issues_404_unknown_user(client: TestClient, pg_users):
    resp = client.get(
        f"/api/v1/users/{UID_GHOST}/issues",
        params={"kind": "assigned"},
        headers=_auth(UID_ANA),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"

    stats = client.get(
        f"/api/v1/users/{UID_GHOST}/issue-stats", headers=_auth(UID_ANA)
    )
    assert stats.status_code == 404


def test_user_issues_401_without_token(client: TestClient, pg_users):
    resp = client.get(
        f"/api/v1/users/{UID_ANA}/issues", params={"kind": "assigned"}
    )
    assert resp.status_code == 401

    stats = client.get(f"/api/v1/users/{UID_ANA}/issue-stats")
    assert stats.status_code == 401


def test_user_issues_invalid_kind_422(client: TestClient, pg_users):
    resp = client.get(
        f"/api/v1/users/{UID_ANA}/issues",
        params={"kind": "nonsense"},
        headers=_auth(UID_ANA),
    )
    assert resp.status_code == 422
    assert "invalid kind" in resp.json()["detail"]
