"""Unit tests for the workflow definition library router (issue #575).

Builtin ``.md`` imports are read-only; custom workflows carry the creating
user's PG uid. Library only — no execution engine.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from socialseed_tasker.auth.user_store import PostgresWorkflowStore
from socialseed_tasker.infrastructure.web_api import workflows_seed
from socialseed_tasker.infrastructure.web_api.routers import workflows
from socialseed_tasker.infrastructure.web_api.schemas import WorkflowCreate, WorkflowUpdate
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg


def _install_env(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor, user: str | None = "admin") -> None:
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(workflows, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(workflows, "_resolve_user", lambda _request: user)


def _seed_builtin(cursor: FakePgCursor, slug: str = "implement-issue", name: str = "Implement an Issue") -> None:
    PostgresWorkflowStore("postgresql://fake").seed_builtin(
        [{"slug": slug, "name": name, "description": "when to use", "content_md": "# Workflow: x\n\nbody"}]
    )


def _request() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# GET /workflows + GET /workflows/{slug} (issue #575)
# ---------------------------------------------------------------------------


def test_list_and_get_workflow_by_slug(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)
    _seed_builtin(cursor)
    created = workflows.create_workflow(
        WorkflowCreate(slug="my-flow", name="My Flow", description="d", content_md="# My Flow\n\nsteps"),
        _request(),
    )
    assert created.data.created_by == "admin"
    assert created.data.source == "custom"

    listed = workflows.list_workflows(source=None)
    assert [w.slug for w in listed.data] == ["implement-issue", "my-flow"]
    assert listed.data[0].content_md is None  # list rows omit content

    fetched = workflows.get_workflow("my-flow")
    assert fetched.data.content_md == "# My Flow\n\nsteps"
    assert fetched.data.created_by == "admin"

    custom_only = workflows.list_workflows(source="custom")
    assert [w.slug for w in custom_only.data] == ["my-flow"]


def test_get_workflow_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        workflows.get_workflow("ghost")

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# POST /workflows (issue #575)
# ---------------------------------------------------------------------------


def test_create_custom_workflow_sets_created_by_uid(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor, user="uid-ana")

    created = workflows.create_workflow(
        WorkflowCreate(slug="release-flow", name="Release", content_md="# Release\n\nship it"),
        _request(),
    )

    assert created.data.created_by == "uid-ana"
    assert created.data.source == "custom"
    assert cursor.workflows["release-flow"]["created_by"] == "uid-ana"


def test_create_duplicate_slug_409(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)
    _seed_builtin(cursor)

    with pytest.raises(HTTPException) as exc:
        workflows.create_workflow(WorkflowCreate(slug="implement-issue", name="Dup"), _request())

    assert exc.value.status_code == 409


def test_create_invalid_slug_422(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)

    with pytest.raises(ValidationError):
        WorkflowCreate(slug="Bad Slug!", name="x")


# ---------------------------------------------------------------------------
# PUT /workflows/{slug} (issue #575)
# ---------------------------------------------------------------------------


def test_update_custom_workflow_partial(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)
    workflows.create_workflow(WorkflowCreate(slug="my-flow", name="My Flow", content_md="v1"), _request())

    updated = workflows.update_workflow("my-flow", WorkflowUpdate(name="Renamed", content_md="v2"))

    assert updated.data.name == "Renamed"
    assert updated.data.content_md == "v2"
    assert updated.data.updated_at is not None


def test_builtin_workflow_not_editable_409(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)
    _seed_builtin(cursor)

    with pytest.raises(HTTPException) as exc:
        workflows.update_workflow("implement-issue", WorkflowUpdate(name="Hacked"))

    assert exc.value.status_code == 409
    assert cursor.workflows["implement-issue"]["name"] == "Implement an Issue"


def test_update_missing_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        workflows.update_workflow("ghost", WorkflowUpdate(name="x"))

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /workflows/{slug} (issue #575)
# ---------------------------------------------------------------------------


def test_delete_custom_workflow_200_and_user_delete_sets_null(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor, user="uid-ana")
    workflows.create_workflow(WorkflowCreate(slug="temp-flow", name="Temp"), _request())

    deleted = workflows.delete_workflow("temp-flow")

    assert deleted.data is True
    assert "temp-flow" not in cursor.workflows

    with pytest.raises(HTTPException) as exc:
        workflows.delete_workflow("temp-flow")
    assert exc.value.status_code == 404


def test_deleting_the_creator_keeps_the_workflow_created_by_null(monkeypatch: pytest.MonkeyPatch):
    """DDL created_by ON DELETE SET NULL: removing the user never removes the workflow (#575)."""
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor, user="uid-ana")
    cursor.users["uid-ana"] = {
        "id": "uid-ana",
        "username": "ana",
        "username_normalized": "ana",
        "user_type": "agent",
        "created_at": None,
    }
    workflows.create_workflow(WorkflowCreate(slug="keep-flow", name="Keep"), _request())

    from socialseed_tasker.auth.user_store import PostgresAgentProfileStore

    assert PostgresAgentProfileStore("postgresql://fake").delete_profile("uid-ana") is True

    assert "keep-flow" in cursor.workflows
    assert cursor.workflows["keep-flow"]["created_by"] is None


def test_delete_builtin_409(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)
    _seed_builtin(cursor)

    with pytest.raises(HTTPException) as exc:
        workflows.delete_workflow("implement-issue")

    assert exc.value.status_code == 409
    assert "implement-issue" in cursor.workflows


# ---------------------------------------------------------------------------
# 503 sin database (patrón #564/#572/#574)
# ---------------------------------------------------------------------------


def test_workflows_503_without_database_url(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)
    monkeypatch.setattr(workflows, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        workflows.list_workflows()

    assert exc.value.status_code == 503


# ---------------------------------------------------------------------------
# Seed idempotente de los .md builtin (issue #575)
# ---------------------------------------------------------------------------


def test_seed_workflows_imports_builtin_markdown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    cursor = FakePgCursor()
    _install_env(monkeypatch, cursor)
    (tmp_path / "implement-issue.md").write_text(
        "# Workflow: Implement an Issue\n\nWhen instructed to implement a Tasker issue.\n\n## Steps\n",
        encoding="utf-8",
    )
    (tmp_path / "commit-push.md").write_text(
        "# Workflow: Prepare for Commit\n\nRequires user approval.\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Not a workflow\n", encoding="utf-8")
    monkeypatch.setenv("TASKER_WORKFLOWS_DIR", str(tmp_path))
    monkeypatch.setattr(workflows_seed, "_ASSETS_DIR", tmp_path / "empty-assets")

    first = workflows_seed.seed_workflows("postgresql://fake")
    assert first == {"total": 2, "inserted": 2}
    assert cursor.workflows["implement-issue"]["source"] == "builtin"
    assert cursor.workflows["implement-issue"]["name"] == "Implement an Issue"
    assert cursor.workflows["implement-issue"]["description"] == "When instructed to implement a Tasker issue."
    assert "commit-push" in cursor.workflows
    assert "README" not in cursor.workflows

    # second run never duplicates nor overwrites
    cursor.workflows["implement-issue"]["name"] = "User Edit"
    second = workflows_seed.seed_workflows("postgresql://fake")
    assert second == {"total": 2, "inserted": 0}
    assert cursor.workflows["implement-issue"]["name"] == "User Edit"


def test_seed_workflows_collects_repo_and_assets(monkeypatch: pytest.MonkeyPatch):
    """Without overrides the collector finds the repo .agent/workflows files."""
    monkeypatch.delenv("TASKER_WORKFLOWS_DIR", raising=False)

    entries = workflows_seed.collect_builtin_workflows()
    slugs = {entry["slug"] for entry in entries}

    assert len(entries) >= 5
    assert "implement-issue" in slugs
