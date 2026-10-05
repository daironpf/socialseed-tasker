"""Tests for the setup wizard endpoints (issues #543/#549).

Runs without containers or network: the Neo4j setup store is replaced by an
in-memory fake and ``create_user`` (PostgreSQL bcrypt) is monkeypatched, the
same pattern used by ``test_chat_endpoints.py``. The welcome-notification
flow (#549) injects a fake notifications repository (#547) on app.state.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import socialseed_tasker.infrastructure.web_api.routers.setup as setup_api
from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.mongo.notification_repository import (
    NotificationStoreError,
)
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers.realtime import RealtimeHub
from socialseed_tasker.models.notification import (
    Notification,
    NotificationSeverity,
    NotificationType,
)

# Welcome payload literal from notas.md (issue #549), restated here so the
# test locks the exact copy instead of reusing the production constants.
WELCOME_TITLE = "¡Bienvenido a SocialSeed Tasker!"
WELCOME_MESSAGE = (
    "El sistema ha sido instalado correctamente. Te recomendamos "
    "crear tus primeros agentes de IA y registrar usuarios en la plataforma."
)


class FakeSetupStore:
    def __init__(self) -> None:
        self.installed_flag = False
        self.fail = False
        self.count_fail = False
        self.nodes = 0
        self.wipe_calls = 0
        self.initialized: dict[str, Any] | None = None

    def installed(self) -> bool:
        if self.fail:
            raise setup_api.SetupStoreError("neo4j down")
        return self.installed_flag or self.initialized is not None

    def node_count(self) -> int:
        if self.fail or self.count_fail:
            raise setup_api.SetupStoreError("neo4j down")
        return self.nodes

    def wipe(self) -> None:
        if self.fail:
            raise setup_api.SetupStoreError("neo4j down")
        self.wipe_calls += 1

    def initialize(
        self,
        *,
        admin_username: str,
        project_name: str,
        project_summary: str,
        policies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if self.fail:
            raise setup_api.SetupStoreError("neo4j down")
        self.initialized = {
            "admin_username": admin_username,
            "project_name": project_name,
            "project_summary": project_summary,
            "policies": policies,
        }
        return {"projectId": "project-1"}


class FakeSecretsStore:
    def __init__(self) -> None:
        self.secrets: dict[str, dict[str, Any]] = {}

    def put_secret(
        self,
        name: str,
        value: bytes,
        metadata: dict[str, Any] | None = None,
        actor: str | None = None,
    ) -> None:
        self.secrets[name] = {"value": value, "metadata": metadata or {}, "actor": actor}

    def get_secret(self, name: str, reveal: bool = False) -> dict[str, Any]:
        if name not in self.secrets:
            raise KeyError(name)
        entry = self.secrets[name]
        result: dict[str, Any] = {"metadata": entry["metadata"], "ts": 0}
        if reveal:
            result["value"] = entry["value"]
        return result


@pytest.fixture()
def setup_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TASKER_AUTH_ENABLED", "true")
    monkeypatch.setenv("TASKER_API_KEY", "test-token")
    for name in (
        "TASKER_INSTALLED",
        "TASKER_DATABASE_URL",
        "TASKER_MONGO_URL",
        "TASKER_REDIS_URL",
        "TASKER_INTEGRATION",
        "TASKER_AUTH_SEED",
        "TASKER_RATE_LIMIT_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    app = create_app()
    store = FakeSetupStore()
    app.state.setup_store = store
    user_calls: list[dict[str, Any]] = []

    def _fake_create_user(**kwargs: Any) -> str:
        user_calls.append(kwargs)
        return "created"

    monkeypatch.setattr(setup_api, "create_user", _fake_create_user)
    pg_wipes: list[str] = []

    def _fake_wipe_postgres() -> int:
        pg_wipes.append("wipe")
        return 1

    monkeypatch.setattr(setup_api, "wipe_postgres_data", _fake_wipe_postgres)
    secrets_store = FakeSecretsStore()
    fake_container = SimpleNamespace(secrets_store=secrets_store)
    monkeypatch.setattr(
        "socialseed_tasker.cli.wiring.build_default_container",
        lambda: fake_container,
    )
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            store=store,
            user_calls=user_calls,
            pg_wipes=pg_wipes,
            secrets_store=secrets_store,
        )


def _payload(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "admin_user": "admin",
        "admin_password": "admin",
        "project_name": "Mi Proyecto",
        "project_summary": "Resumen inicial",
        "policies": [],
        "custom_policies": [],
    }
    body.update(overrides)
    return body


class FakeWelcomeRepository:
    """Minimal in-memory stand-in for NotificationMongoRepository (#547)."""

    def __init__(self) -> None:
        self.notes: dict[str, Notification] = {}
        self.insert_calls = 0
        self.degraded = False

    def _guard(self, action: str) -> None:
        if self.degraded:
            raise NotificationStoreError(f"{action} unavailable")

    async def list_for_user(
        self,
        user_id: str,
        *,
        read: bool | None = None,
        notification_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        self._guard("list")
        matched = [n for n in self.notes.values() if n.user_id == user_id]
        if read is not None:
            matched = [n for n in matched if n.read is read]
        if notification_type:
            matched = [n for n in matched if n.type.value == notification_type]
        matched.sort(key=lambda n: n.created_at, reverse=True)
        return matched[offset : offset + limit], len(matched)

    async def insert(self, notification: Notification) -> Notification:
        self._guard("insert")
        self.insert_calls += 1
        note = notification.model_copy(update={"id": f"fake-{self.insert_calls}"})
        self.notes[note.id] = note
        return note


def _use_welcome_repo(setup_env: SimpleNamespace) -> FakeWelcomeRepository:
    repository = FakeWelcomeRepository()
    setup_env.client.app.state.notification_repository = repository
    return repository


def _seed_welcome(repository: FakeWelcomeRepository, note_id: str = "existing") -> None:
    repository.notes[note_id] = Notification(
        user_id="admin",
        type=NotificationType.WELCOME,
        severity=NotificationSeverity.INFO,
        title=WELCOME_TITLE,
        message=WELCOME_MESSAGE,
        channel="system",
        requires_action=True,
        link_to="/users",
    )


def test_status_reports_pending_install_without_credentials(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"] == {"installed": False, "needSetup": True}


def test_status_env_override_forces_installed(setup_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKER_INSTALLED", "true")
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    assert resp.json()["data"] == {"installed": True, "needSetup": False}


def test_status_degrades_to_env_when_store_unavailable(
    setup_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_env.store.fail = True
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    assert resp.json()["data"]["installed"] is False

    monkeypatch.setenv("TASKER_INSTALLED", "true")
    resp = setup_env.client.get("/api/v1/setup/status")
    assert resp.status_code == 200
    assert resp.json()["data"]["installed"] is True


def test_initialize_creates_admin_project_and_policies(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(
            admin_user="  Ad@min!  ",
            admin_password="",
            project_name="  Mi Proyecto  ",
            policies=["prevent_circular_dependencies", "require_solution_summary"],
            custom_policies=["Polimorfismo estricto en tipos de nodos"],
        ),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["installed"] is True
    assert data["adminUsername"] == "admin"
    assert data["projectName"] == "Mi Proyecto"
    assert data["projectId"] == "project-1"
    assert data["credentials"] == "created"
    assert len(data["policies"]) == 3

    assert setup_env.user_calls == [
        {"username": "admin", "password": "admin", "role": "ADMIN", "user_type": "admin"}
    ]

    initialized = setup_env.store.initialized
    assert initialized is not None
    assert initialized["admin_username"] == "admin"
    assert initialized["project_name"] == "Mi Proyecto"
    assert initialized["project_summary"] == "Resumen inicial"
    keys = [spec["key"] for spec in initialized["policies"]]
    assert keys == [
        "prevent_circular_dependencies",
        "require_solution_summary",
        "custom:Polimorfismo estricto en tipos de nodos",
    ]

    status = setup_env.client.get("/api/v1/setup/status")
    assert status.json()["data"] == {"installed": True, "needSetup": False}


def test_initialize_falls_back_to_default_credentials(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(admin_user="", admin_password="", project_name="Demo"),
    )
    assert resp.status_code == 200
    assert setup_env.user_calls[0]["username"] == "admin"
    assert setup_env.user_calls[0]["password"] == "admin"


def test_initialize_wipes_all_stores_before_creating(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    assert setup_env.store.wipe_calls == 1
    assert setup_env.pg_wipes == ["wipe"]
    assert setup_env.store.initialized is not None

    status = setup_env.client.get("/api/v1/setup/status")
    assert status.json()["data"]["installed"] is True
    assert setup_env.store.wipe_calls == 1


def test_initialize_maps_all_predefined_policies(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(policies=list(setup_api.PREDEFINED_POLICIES)),
    )
    assert resp.status_code == 200
    specs = setup_env.store.initialized["policies"]
    assert [spec["key"] for spec in specs] == [
        "prevent_circular_dependencies",
        "require_solution_summary",
        "require_human_approval_core",
    ]
    assert {spec["severity"] for spec in specs} == {"BLOCKER", "WARNING"}
    assert all(spec["logic_definition"] for spec in specs)


def test_initialize_returns_403_when_already_installed(setup_env: SimpleNamespace) -> None:
    setup_env.store.installed_flag = True
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 403
    assert setup_env.store.initialized is None
    assert setup_env.store.wipe_calls == 0
    assert setup_env.pg_wipes == []


def test_initialize_rejects_unknown_policy_key(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(policies=["not_a_policy"]),
    )
    assert resp.status_code == 400
    assert setup_env.store.initialized is None
    assert setup_env.store.wipe_calls == 0
    assert setup_env.pg_wipes == []


def test_initialize_requires_project_name(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(project_name="   "),
    )
    assert resp.status_code == 400
    assert setup_env.store.initialized is None
    assert setup_env.store.wipe_calls == 0
    assert setup_env.pg_wipes == []


def test_initialize_skips_postgres_when_not_configured(
    setup_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    from socialseed_tasker.auth import user_store

    monkeypatch.setattr(setup_api, "create_user", user_store.create_user)
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    assert resp.json()["data"]["credentials"] == "skipped"


def test_initialize_fails_with_503_when_store_unavailable(setup_env: SimpleNamespace) -> None:
    setup_env.store.fail = True
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 503
    assert setup_env.store.initialized is None
    assert setup_env.store.wipe_calls == 0
    assert setup_env.pg_wipes == []


def test_initialize_requires_confirm_wipe_when_system_has_data(setup_env: SimpleNamespace) -> None:
    setup_env.store.nodes = 42
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 400
    assert "confirm_wipe" in resp.text
    assert setup_env.store.initialized is None
    assert setup_env.store.wipe_calls == 0
    assert setup_env.pg_wipes == []


def test_initialize_with_confirm_wipe_wipes_populated_system(setup_env: SimpleNamespace) -> None:
    setup_env.store.nodes = 42
    resp = setup_env.client.post(
        "/api/v1/setup/initialize", json=_payload(confirm_wipe=True)
    )
    assert resp.status_code == 200
    assert setup_env.store.wipe_calls == 1
    assert setup_env.pg_wipes == ["wipe"]


def test_initialize_fails_closed_when_node_count_unavailable(setup_env: SimpleNamespace) -> None:
    setup_env.store.count_fail = True
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 503
    assert setup_env.store.initialized is None
    assert setup_env.store.wipe_calls == 0
    assert setup_env.pg_wipes == []


def test_initialize_generates_master_api_key(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["apiKey"].startswith("tasker_sk_live_")
    assert len(data["apiKey"]) > len("tasker_sk_live_") + 20
    assert data["mcpPort"] == 0
    assert setup_env.client.app.state.master_api_key == data["apiKey"]


def test_initialize_accepts_optional_api_key_and_mcp_port(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(api_key="tasker_sk_live_provided", mcp_port=8888),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["apiKey"] == "tasker_sk_live_provided"
    assert data["mcpPort"] == 8888


def test_initialize_persists_master_key_in_secrets_store(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(api_key="tasker_sk_live_persisted", mcp_port=9000),
    )
    assert resp.status_code == 200
    stored = setup_env.secrets_store.secrets[setup_api.MASTER_KEY_SECRET_NAME]
    assert stored["value"] == b"tasker_sk_live_persisted"
    assert stored["metadata"]["mcpPort"] == 9000
    assert stored["metadata"]["source"] == "setup"


def test_initialize_rejects_out_of_range_mcp_port(setup_env: SimpleNamespace) -> None:
    resp = setup_env.client.post(
        "/api/v1/setup/initialize",
        json=_payload(mcp_port=70000),
    )
    assert resp.status_code == 422
    assert setup_env.store.initialized is None


def test_master_api_key_authenticates_requests(setup_env: SimpleNamespace) -> None:
    # Env API key keeps working as before.
    resp = setup_env.client.get(
        "/api/v1/mcp/servers", headers={"X-API-Key": "test-token"}
    )
    assert resp.status_code == 200

    # Without any key the request is rejected.
    resp = setup_env.client.get("/api/v1/mcp/servers")
    assert resp.status_code == 401

    # Initialize issues the master key.
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    master_key = resp.json()["data"]["apiKey"]

    # The in-process key authenticates agent requests (MCP X-API-Key).
    resp = setup_env.client.get(
        "/api/v1/mcp/servers", headers={"X-API-Key": master_key}
    )
    assert resp.status_code == 200

    # A wrong key with the same prefix is still rejected.
    resp = setup_env.client.get(
        "/api/v1/mcp/servers", headers={"X-API-Key": "tasker_sk_live_wrong"}
    )
    assert resp.status_code == 401

    # Simulate an API restart: the key is lazily reloaded from the store.
    setup_env.client.app.state.master_api_key = None
    setup_env.client.app.state.master_api_key_loaded = False
    resp = setup_env.client.get(
        "/api/v1/mcp/servers", headers={"X-API-Key": master_key}
    )
    assert resp.status_code == 200
    assert setup_env.client.app.state.master_api_key == master_key


def test_initialize_inserts_welcome_notification_for_admin(
    setup_env: SimpleNamespace,
) -> None:
    repository = _use_welcome_repo(setup_env)
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    assert repository.insert_calls == 1
    notes = list(repository.notes.values())
    assert len(notes) == 1
    note = notes[0]
    assert note.user_id == "admin"
    assert note.type is NotificationType.WELCOME
    assert note.severity is NotificationSeverity.INFO
    assert note.channel == "system"
    assert note.title == WELCOME_TITLE
    assert note.message == WELCOME_MESSAGE
    assert note.requires_action is True
    assert note.link_to == "/users"
    assert note.read is False


def test_initialize_emits_welcome_event_to_open_stream(
    setup_env: SimpleNamespace,
) -> None:
    # Issue #550: the welcome insert goes through the single publication
    # point, so an admin with /notifications/stream already open receives
    # notification_created reactively instead of only via polling.
    _use_welcome_repo(setup_env)
    hub = RealtimeHub()
    setup_env.client.app.state.realtime_hub = hub
    queue = hub.subscribe_notifications("admin")
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    entry = queue.get_nowait()
    assert entry["event"] == "notification_created"
    data = entry["data"]
    assert data["userId"] == "admin"
    assert data["category"] == "welcome"
    assert data["channel"] == "system"
    assert data["title"] == WELCOME_TITLE
    assert data["linkTo"] == "/users"
    assert data["requiresAction"] is True


def test_initialize_does_not_duplicate_existing_welcome(
    setup_env: SimpleNamespace,
) -> None:
    # Idempotency guard by (user_id, type): a WELCOME already present for the
    # admin (e.g. a rerun whose wipe did not clear the collection) is kept
    # as-is instead of inserting a second copy (issue #549 implementation 4).
    repository = _use_welcome_repo(setup_env)
    _seed_welcome(repository)
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    assert repository.insert_calls == 0
    assert len(repository.notes) == 1


def test_reinstall_with_confirm_wipe_leaves_exactly_one_welcome(
    setup_env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _use_welcome_repo(setup_env)
    _seed_welcome(repository)
    repository.notes["stale-mention"] = Notification(
        user_id="admin",
        type=NotificationType.MENTION,
        severity=NotificationSeverity.INFO,
        title="stale",
        message="stale",
        channel="mention",
    )
    mongo_wipes: list[str] = []

    def _fake_wipe_mongo() -> None:
        # Mirrors the real _wipe_mongo: it drops every collection of the
        # database, notifications included (asserted by
        # test_wipe_mongo_drops_notifications_collection).
        mongo_wipes.append("wipe")
        repository.notes.clear()

    monkeypatch.setattr(setup_api, "_wipe_mongo", _fake_wipe_mongo)
    setup_env.store.nodes = 42
    resp = setup_env.client.post(
        "/api/v1/setup/initialize", json=_payload(confirm_wipe=True)
    )
    assert resp.status_code == 200
    assert mongo_wipes == ["wipe"]
    assert len(repository.notes) == 1
    note = next(iter(repository.notes.values()))
    assert note.type is NotificationType.WELCOME
    assert note.title == WELCOME_TITLE
    assert note.user_id == "admin"


def test_initialize_succeeds_when_notification_store_fails(
    setup_env: SimpleNamespace,
) -> None:
    repository = _use_welcome_repo(setup_env)
    repository.degraded = True
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    assert setup_env.store.initialized is not None
    assert repository.insert_calls == 0


def test_initialize_succeeds_without_mongo_configured(
    setup_env: SimpleNamespace,
) -> None:
    # No fake injected: the real repository (TASKER_MONGO_URL unset by the
    # fixture) raises the typed NotificationStoreError, which the welcome
    # insert must swallow so the installation still succeeds (AC #549).
    assert setup_env.client.app.state.notification_repository is not None
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200
    assert setup_env.store.initialized is not None


def test_wipe_mongo_drops_notifications_collection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TASKER_MONGO_URL", "mongodb://localhost:27017/tasker_chat")
    dropped: list[str] = []

    class _FakeDatabase:
        def list_collection_names(self) -> list[str]:
            return ["conversations", "messages", "notifications"]

        def drop_collection(self, name: str) -> None:
            dropped.append(name)

    database = _FakeDatabase()

    class _FakeMongoClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __getitem__(self, name: str) -> Any:
            assert name == "tasker_chat"
            return database

        def close(self) -> None:
            pass

    monkeypatch.setattr("pymongo.MongoClient", _FakeMongoClient)
    setup_api._wipe_mongo()
    assert dropped == ["conversations", "messages", "notifications"]


def test_first_login_lists_welcome_notification(setup_env: SimpleNamespace) -> None:
    # AC #549: the first /api/v1/notifications payload after install
    # (#548) includes the seeded welcome for the created admin.
    _use_welcome_repo(setup_env)
    resp = setup_env.client.post("/api/v1/setup/initialize", json=_payload())
    assert resp.status_code == 200

    tokens = issue_tokens({"id": "admin", "username": "admin"})
    listing = setup_env.client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert listing.status_code == 200
    items = listing.json()["data"]
    assert len(items) == 1
    welcome = items[0]
    assert welcome["type"] == "WELCOME"
    assert welcome["category"] == "welcome"
    assert welcome["userId"] == "admin"
    assert welcome["title"] == WELCOME_TITLE
    assert welcome["linkTo"] == "/users"
    assert welcome["requiresAction"] is True
