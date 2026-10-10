"""Unit tests for the PostgreSQL catalog endpoints (issue #572).

``GET /skills`` and ``GET /tools`` expose the catalogs seeded by #558 that
the frontend pickers consume; the tools 422 contract of ``/agents/profiles``
is shared with #564 (``test_agent_profiles_api.test_create_agent_profile_unknown_tool_422``).
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from socialseed_tasker.auth.user_store import TOOLS_SEED, PostgresUserStore
from socialseed_tasker.infrastructure.web_api.routers import catalogs as catalogs_module
from socialseed_tasker.infrastructure.web_api.routers.catalogs import list_skills, list_tools
from tests.fakes.fake_pg_users import FakePgCursor, ScriptedCursor, install_fake_pg


def _store(monkeypatch: pytest.MonkeyPatch, cursor: Any) -> PostgresUserStore:
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(catalogs_module, "get_database_url", lambda: "postgresql://fake")
    return PostgresUserStore("postgresql://fake")


class TestSkillsCatalog:
    def test_get_skills_returns_catalog(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = ScriptedCursor(fetchall_rows=[("python", "Python"), ("vue", "Vue")])
        _store(monkeypatch, cursor)

        response = list_skills()

        sql = cursor.statements[-1][0]
        assert "SELECT id, name FROM skills" in sql
        assert "ORDER BY name" in sql
        items = response.data
        assert [item.id for item in items] == ["python", "vue"]
        assert [item.name for item in items] == ["Python", "Vue"]

    def test_get_skills_empty_catalog(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = ScriptedCursor(fetchall_rows=[])
        _store(monkeypatch, cursor)

        assert list_skills().data == []


class TestToolsCatalog:
    def test_get_tools_returns_catalog(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = ScriptedCursor(
            fetchall_rows=[
                ("code_search", "Code search", "Search the codebase"),
                ("shell", "Shell", None),
            ]
        )
        _store(monkeypatch, cursor)

        response = list_tools()

        sql = cursor.statements[-1][0]
        assert "SELECT id, name, description FROM tools" in sql
        assert "ORDER BY name" in sql
        first, second = response.data
        assert (first.id, first.name, first.description) == (
            "code_search",
            "Code search",
            "Search the codebase",
        )
        assert (second.id, second.name, second.description) == ("shell", "Shell", None)

    def test_catalog_serves_the_seeded_snake_case_slugs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Canonical slugs of the #558 seed: the single source that ends the divergence (#572)."""
        cursor = ScriptedCursor(fetchall_rows=list(TOOLS_SEED))
        _store(monkeypatch, cursor)

        ids = [item.id for item in list_tools().data]

        assert ids == [slug for slug, _, _ in TOOLS_SEED]
        assert all("-" not in slug and slug == slug.lower() for slug in ids)  # snake_case, never kebab


class TestCatalogsAvailability:
    def test_catalogs_503_without_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(catalogs_module, "get_database_url", lambda: None)

        for endpoint in (list_skills, list_tools):
            with pytest.raises(HTTPException) as exc:
                endpoint()
            assert exc.value.status_code == 503
            assert "TASKER_DATABASE_URL" in str(exc.value.detail)


class TestCatalogWritesFeedTheReads:
    def test_create_user_unknown_skill_is_upserted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Free skill values land in the catalog on save (picker contract, #559/#572)."""
        from socialseed_tasker.auth.user_store import hash_password

        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        uid = store.create_human_user(
            username="ana",
            email="ana@x.com",
            role_id="VIEWER",
            skills=["Quantum Computing"],
            password_hash=hash_password("sesamo"),
        )

        assert uid in cursor.user_skills
        assert "quantum-computing" in cursor.user_skills[uid]
        assert cursor.skills["quantum-computing"] == "Quantum Computing"
