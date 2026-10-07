"""Auth sessions in Redis with in-memory fallback (issue #527)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth import tokens
from socialseed_tasker.auth.redis_sessions import AuthSessionStore, session_key
from socialseed_tasker.auth.user_store import authenticate_user, normalize_username
from socialseed_tasker.infrastructure.web_api.app import create_app


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> AuthSessionStore:
    monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
    return AuthSessionStore()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
    monkeypatch.delenv("TASKER_DATABASE_URL", raising=False)
    monkeypatch.setenv("TASKER_AUTH_ENABLED", "true")
    monkeypatch.setenv("TASKER_API_KEY", "test-api-key")
    monkeypatch.setenv(
        "TASKER_AUTH_USERS",
        json.dumps({"alice": {"token": "k-alice", "username": "alice", "permissions": ["create:issue"]}}),
    )
    return TestClient(create_app())


def _fake_authenticate(_url: str, username: str, password: str) -> dict[str, Any] | None:
    if password != normalize_username(username):
        return None
    return {"id": "manolo", "username": "manolo", "email": None, "role": "developer", "type": "person"}


@pytest.fixture
def pg_login(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_DATABASE_URL", "postgresql://user:pass@localhost:5432/tasker")
    monkeypatch.setattr(
        "socialseed_tasker.infrastructure.web_api.routers.auth.authenticate_user",
        _fake_authenticate,
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, headers: dict[str, str] | None = None, **payload: Any) -> dict[str, Any]:
    resp = client.post("/api/v1/auth/login", json=payload, headers=headers or {})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _session_of(client: TestClient, access_token: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    claims = tokens.verify_access(access_token)
    assert claims is not None and claims.get("sid")
    session = client.app.state.auth_sessions.get(str(claims["sub"]), str(claims["sid"]))
    return claims, session


class TestSessionStore:
    def test_key_format(self) -> None:
        assert session_key("user-1", "sess-1") == "session:user-1:sess-1"

    def test_defaults_to_memory_without_redis_url(self, store: AuthSessionStore) -> None:
        assert store.backend == "memory"

    def test_save_get_delete_roundtrip(self, store: AuthSessionStore) -> None:
        payload = {"session_id": "s1", "user_id": "u1", "permissions": ["read:context"]}
        store.save("u1", "s1", payload, 604800)
        assert store.get("u1", "s1") == payload
        store.delete("u1", "s1")
        assert store.get("u1", "s1") is None

    def test_expired_session_is_not_returned(self, store: AuthSessionStore) -> None:
        store.save("u1", "s1", {"a": 1}, -1)
        assert store.get("u1", "s1") is None

    def test_delete_all_for_user_removes_only_that_users_sessions(self, store: AuthSessionStore) -> None:
        store.save("u1", "s1", {"n": 1}, 60)
        store.save("u1", "s2", {"n": 2}, 60)
        store.save("u2", "s1", {"n": 3}, 60)
        assert store.delete_all_for_user("u1") == 2
        assert store.get("u1", "s1") is None
        assert store.get("u1", "s2") is None
        assert store.get("u2", "s1") == {"n": 3}
        assert store.delete_all_for_user("u1") == 0

    def test_falls_back_to_memory_when_redis_is_unreachable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
        store = AuthSessionStore(redis_url="invalid://not-redis")
        assert store.backend == "memory"
        store.save("u1", "s1", {"a": 1}, 60)
        assert store.get("u1", "s1") == {"a": 1}


class TestSessionClaims:
    def test_issue_tokens_carries_session_id(self) -> None:
        user = {"id": "u-sid-1", "username": "u-sid-1", "role": "DEVELOPER", "permissions": ["read:context"]}
        pair = tokens.issue_tokens(user, session_id="sess-abc")
        access = tokens.verify_access(pair["access_token"])
        refresh = tokens.peek(pair["refresh_token"])
        assert access is not None and access.get("sid") == "sess-abc"
        assert refresh is not None and refresh.get("sid") == "sess-abc"

    def test_rotate_carries_session_id_forward(self) -> None:
        user = {"id": "u-sid-2", "username": "u-sid-2", "role": "DEVELOPER", "permissions": ["read:context"]}
        pair = tokens.issue_tokens(user, session_id="sess-xyz")
        rotated = tokens.rotate(pair["refresh_token"])
        assert rotated is not None
        access = tokens.verify_access(rotated["access_token"])
        assert access is not None and access.get("sid") == "sess-xyz"

    def test_tokens_without_session_have_no_sid(self) -> None:
        pair = tokens.issue_tokens({"id": "u-sid-3", "permissions": ["read:context"]})
        access = tokens.verify_access(pair["access_token"])
        refresh = tokens.peek(pair["refresh_token"])
        assert access is not None and "sid" not in access
        assert refresh is not None and "sid" not in refresh

    def test_revoke_all_for_subject_drops_active_refresh_tokens(self) -> None:
        pair = tokens.issue_tokens({"id": "u-revoke", "username": "u-revoke", "role": "VIEWER"})
        assert tokens.verify_refresh(pair["refresh_token"]) is not None
        tokens.revoke_all_for_subject("u-revoke")
        assert tokens.verify_refresh(pair["refresh_token"]) is None


class TestAuthenticateUser:
    def test_empty_credentials_return_none_without_connecting(self) -> None:
        url = "postgresql://user:pass@localhost:5432/tasker"
        assert authenticate_user(url, "", "x") is None
        assert authenticate_user(url, "somebody", "") is None


class TestPasswordLogin:
    def test_login_issues_tokens_and_persists_session(self, client: TestClient, pg_login: None) -> None:
        data = _login(client, headers={"User-Agent": "pytest-agent"}, username="Manolo", password="manolo")
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == "manolo"
        assert data["user"]["role"] == "DEVELOPER"
        claims, session = _session_of(client, data["access_token"])
        assert session is not None
        assert session["user_agent"] == "pytest-agent"
        assert session["permissions"] == data["user"]["permissions"]

    def test_admin_database_role_maps_to_admin(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TASKER_DATABASE_URL", "postgresql://user:pass@localhost:5432/tasker")
        monkeypatch.setattr(
            "socialseed_tasker.infrastructure.web_api.routers.auth.authenticate_user",
            lambda *_args, **_kwargs: {"id": "boss", "username": "boss", "email": None, "role": "admin"},
        )
        data = _login(client, username="boss", password="boss")
        assert data["user"]["role"] == "ADMIN"
        assert "admin" in data["user"]["permissions"]

    def test_wrong_password_is_401(self, client: TestClient, pg_login: None) -> None:
        resp = client.post("/api/v1/auth/login", json={"username": "Manolo", "password": "otra-contrasena"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid username or password"

    def test_missing_database_url_is_503(self, client: TestClient) -> None:
        resp = client.post("/api/v1/auth/login", json={"username": "manolo", "password": "manolo"})
        assert resp.status_code == 503

    def test_empty_body_is_400(self, client: TestClient) -> None:
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 400

    def test_partial_credentials_are_400(self, client: TestClient) -> None:
        assert client.post("/api/v1/auth/login", json={"username": "manolo"}).status_code == 400
        assert client.post("/api/v1/auth/login", json={"password": "manolo"}).status_code == 400


class TestApiKeyLogin:
    def test_api_key_login_still_works(self, client: TestClient) -> None:
        data = _login(client, api_key="k-alice")
        assert data["user"]["id"] == "alice"
        claims, session = _session_of(client, data["access_token"])
        assert session is not None
        assert session["session_id"] == claims.get("sid")

    def test_invalid_api_key_is_401(self, client: TestClient) -> None:
        resp = client.post("/api/v1/auth/login", json={"api_key": "bad-key"})
        assert resp.status_code == 401


class TestSessionLifecycle:
    def test_me_works_with_live_session(self, client: TestClient, pg_login: None) -> None:
        data = _login(client, username="manolo", password="manolo")
        resp = client.get("/api/v1/auth/me", headers=_bearer(data["access_token"]))
        assert resp.status_code == 200
        assert resp.json()["username"] == "manolo"

    def test_logout_deletes_session_and_revokes_access(self, client: TestClient, pg_login: None) -> None:
        data = _login(client, username="manolo", password="manolo")
        claims, _ = _session_of(client, data["access_token"])
        out = client.post("/api/v1/auth/logout", json={"refresh_token": data["refresh_token"]})
        assert out.status_code == 200
        assert client.app.state.auth_sessions.get(str(claims["sub"]), str(claims["sid"])) is None
        me = client.get("/api/v1/auth/me", headers=_bearer(data["access_token"]))
        assert me.status_code == 401
        assert me.json()["detail"] == "Session revoked"
        again = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert again.status_code == 401

    def test_logout_with_access_token_only_deletes_session(
        self, client: TestClient, pg_login: None
    ) -> None:
        data = _login(client, username="manolo", password="manolo")
        claims, _ = _session_of(client, data["access_token"])
        out = client.post("/api/v1/auth/logout", json={}, headers=_bearer(data["access_token"]))
        assert out.status_code == 200
        assert client.app.state.auth_sessions.get(str(claims["sub"]), str(claims["sid"])) is None
        me = client.get("/api/v1/auth/me", headers=_bearer(data["access_token"]))
        assert me.status_code == 401

    def test_refresh_rotates_and_updates_session(self, client: TestClient, pg_login: None) -> None:
        data = _login(client, username="manolo", password="manolo")
        claims, before = _session_of(client, data["access_token"])
        assert before is not None
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert resp.status_code == 200
        rotated = resp.json()
        assert rotated["refresh_token"] != data["refresh_token"]
        assert rotated["access_token"] != data["access_token"]
        _, after = _session_of(client, rotated["access_token"])
        assert after is not None
        assert after["session_id"] == claims.get("sid")
        assert after["refresh_jti"] != before["refresh_jti"]
        assert after["created_at"] == before["created_at"]
        reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert reuse.status_code == 401

    def test_refresh_is_rejected_once_the_session_is_revoked(
        self, client: TestClient, pg_login: None
    ) -> None:
        data = _login(client, username="manolo", password="manolo")
        claims, _ = _session_of(client, data["access_token"])
        client.app.state.auth_sessions.delete(str(claims["sub"]), str(claims["sid"]))
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Session revoked"

    def test_middleware_rejects_token_with_revoked_session(
        self, client: TestClient, pg_login: None
    ) -> None:
        data = _login(client, username="manolo", password="manolo")
        headers = _bearer(data["access_token"])
        ok = client.get("/api/v1/does-not-exist", headers=headers)
        assert ok.status_code == 404
        claims, _ = _session_of(client, data["access_token"])
        client.app.state.auth_sessions.delete(str(claims["sub"]), str(claims["sid"]))
        revoked = client.get("/api/v1/does-not-exist", headers=headers)
        assert revoked.status_code == 401
        assert revoked.json()["error"]["code"] == "UNAUTHORIZED"
