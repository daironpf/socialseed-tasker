"""Unit tests for the human skills management endpoints (issue #576).

The catalog lives in ``skills`` and the assignments in ``user_skills`` (both
seeded by #558); these endpoints add granular add/remove per user plus an
explicit catalog create, so the edit modal never needs a full PUT replace.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from socialseed_tasker.auth.user_store import PostgresUserStore
from socialseed_tasker.infrastructure.web_api.routers import catalogs
from socialseed_tasker.infrastructure.web_api.routers import user as user_router
from socialseed_tasker.infrastructure.web_api.schemas import (
    SkillCreateRequest,
    UserSkillAssignRequest,
)
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg


def _install(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> None:
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(catalogs, "get_database_url", lambda: "postgresql://fake")


def _seed_human(cursor: FakePgCursor, skills: list[str] | None = None) -> str:
    uid = "uid-ana"
    cursor.users[uid] = {
        "id": uid,
        "username": "ana",
        "username_normalized": "ana",
        "user_type": "human",
        "created_at": None,
    }
    cursor.human[uid] = {"user_id": uid, "email": "ana@x.com", "role_id": "VIEWER"}
    for name in skills or []:
        slug = name.strip().lower()
        cursor.skills[slug] = name
        cursor.user_skills.setdefault(uid, set()).add(slug)
    return uid


# ---------------------------------------------------------------------------
# POST /skills - explicit catalog creation (issue #576)
# ---------------------------------------------------------------------------


def test_create_skill_201_and_409_on_duplicate(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    created = catalogs.create_skill(SkillCreateRequest(name="CI/CD"))

    assert created.data.id == "ci-cd"
    assert created.data.name == "CI/CD"
    assert cursor.skills["ci-cd"] == "CI/CD"

    with pytest.raises(HTTPException) as exc:
        catalogs.create_skill(SkillCreateRequest(name="CI CD"))

    assert exc.value.status_code == 409
    assert cursor.skills["ci-cd"] == "CI/CD"


# ---------------------------------------------------------------------------
# GET /users/{id}/skills (issue #576)
# ---------------------------------------------------------------------------


def test_list_user_skills_ordered_by_name(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor, skills=["Vue", "Go"])

    response = user_router.list_user_skills(uid)

    assert [item.name for item in response.data] == ["Go", "Vue"]
    assert all(item.user_id == uid for item in response.data)
    assert {item.skill_id for item in response.data} == {"go", "vue"}


def test_list_user_skills_404_when_user_missing(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.list_user_skills("ghost")

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# POST /users/{id}/skills - find-or-create + link (issue #576)
# ---------------------------------------------------------------------------


def test_assign_existing_catalog_skill(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor)
    cursor.skills["python"] = "Python"

    response = user_router.assign_user_skill(uid, UserSkillAssignRequest(name="Python"))

    assert response.data.skill_id == "python"
    assert cursor.user_skills[uid] == {"python"}
    assert cursor.skills["python"] == "Python"  # catalog kept as-is


def test_assign_new_skill_creates_the_catalog_row(monkeypatch: pytest.MonkeyPatch):
    """The 'add a new skill from the same window' path: name not in catalog (#576)."""
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor)

    response = user_router.assign_user_skill(uid, UserSkillAssignRequest(name="Kubernetes"))

    assert response.data.name == "Kubernetes"
    assert cursor.skills["kubernetes"] == "Kubernetes"
    assert cursor.user_skills[uid] == {"kubernetes"}


def test_assign_is_idempotent(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor)

    first = user_router.assign_user_skill(uid, UserSkillAssignRequest(name="Docker"))
    second = user_router.assign_user_skill(uid, UserSkillAssignRequest(name="docker"))

    assert first.data.skill_id == second.data.skill_id == "docker"
    assert cursor.user_skills[uid] == {"docker"}  # no duplicates


def test_assign_404_when_user_missing(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.assign_user_skill("ghost", UserSkillAssignRequest(name="Docker"))

    assert exc.value.status_code == 404


def test_assign_422_on_invalid_name(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.assign_user_skill(uid, UserSkillAssignRequest(name="   "))

    assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /users/{id}/skills/{skill_id} (issue #576)
# ---------------------------------------------------------------------------


def test_unassign_skill_keeps_the_catalog_row(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor, skills=["Python", "Vue"])

    response = user_router.unassign_user_skill(uid, "python")

    assert response.data is True
    assert cursor.user_skills[uid] == {"vue"}
    assert "python" in cursor.skills  # catalog is never touched by unassign


def test_unassign_missing_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor, skills=["Python"])

    with pytest.raises(HTTPException) as exc:
        user_router.unassign_user_skill(uid, "golang")

    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        user_router.unassign_user_skill("ghost", "python")

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# 503 sin database (patrón #564/#572/#574/#575)
# ---------------------------------------------------------------------------


def test_user_skills_503_without_database_url(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    monkeypatch.setattr(user_router, "get_database_url", lambda: None)
    monkeypatch.setattr(catalogs, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        user_router.list_user_skills("any")

    assert exc.value.status_code == 503

    with pytest.raises(HTTPException) as exc:
        catalogs.create_skill(SkillCreateRequest(name="X"))

    assert exc.value.status_code == 503


# ---------------------------------------------------------------------------
# Round-trip con el store real sobre el fake (slug del skill_id)
# ---------------------------------------------------------------------------


def test_skill_ids_are_slugified_end_to_end(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    uid = _seed_human(cursor)

    assigned = user_router.assign_user_skill(uid, UserSkillAssignRequest(name="Machine Learning"))
    listed = user_router.list_user_skills(uid)
    deleted = user_router.unassign_user_skill(uid, assigned.data.skill_id)

    assert assigned.data.skill_id == "machine-learning"
    assert [item.skill_id for item in listed.data] == ["machine-learning"]
    assert deleted.data is True
    assert PostgresUserStore("postgresql://fake").list_user_skills(uid) == []
