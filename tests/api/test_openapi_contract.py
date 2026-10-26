"""OpenAPI contract for write endpoints (issue #595).

Regression guards for the two bugs the audit found: routes with a body
parameter must declare ``requestBody`` in ``app.openapi()``, the audited
endpoints must expose a named component schema (not a generic ``dict``), and
``POST|DELETE /issues/{id}/affects`` must accept the object contract
``{"symbol_id": ...}`` used everywhere else in the API.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def spec(app):
    return app.openapi()


def test_every_body_route_declares_request_body(app, spec) -> None:
    missing: list[str] = []
    for route in app.routes:
        if not hasattr(route, "methods") or not hasattr(route, "dependant"):
            continue
        if not route.dependant.body_params:
            continue
        path_spec = spec["paths"].get(route.path, {})
        for method in route.methods - {"HEAD", "OPTIONS"}:
            if "requestBody" not in path_spec.get(method.lower(), {}):
                missing.append(f"{method} {route.path}")
    assert missing == [], f"endpoints with body params but no requestBody: {missing}"


NAMED_REQUEST_SCHEMAS = [
    ("POST", "/api/v1/epics", "EpicCreateRequest"),
    ("PATCH", "/api/v1/epics/{epic_id}", "EpicUpdateRequest"),
    ("POST", "/api/v1/epics/{epic_id}/issues", "EpicLinkIssuesRequest"),
    ("POST", "/api/v1/objectives", "ObjectiveCreateRequest"),
    ("PATCH", "/api/v1/objectives/{objective_id}", "ObjectiveUpdateRequest"),
    ("POST", "/api/v1/objectives/{objective_id}/epics", "ObjectiveLinkEpicsRequest"),
    ("POST", "/api/v1/secrets", "SecretPutRequest"),
    ("POST", "/api/v1/secrets/rotate", "SecretRotateScheduleRequest"),
    ("POST", "/api/v1/secrets/rotate/run", "SecretRotateRunRequest"),
    ("POST", "/api/v1/admin/flags", "FlagSetRequest"),
    ("POST", "/api/v1/privacy/export", "PrivacyExportRequest"),
    ("POST", "/api/v1/privacy/delete", "PrivacyDeleteRequest"),
    ("POST", "/api/v1/deployments", "DeploymentCreateRequest"),
    ("POST", "/api/v1/models/{model_name}/infer", "InferenceRequest"),
    ("POST", "/api/v1/issues/{issue_id}/affects", "SymbolLinkRequest"),
    ("DELETE", "/api/v1/issues/{issue_id}/affects", "SymbolLinkRequest"),
]


@pytest.mark.parametrize("method,path,schema_name", NAMED_REQUEST_SCHEMAS)
def test_audited_endpoint_declares_named_request_schema(
    spec, method: str, path: str, schema_name: str
) -> None:
    operation = spec["paths"][path][method.lower()]
    schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert schema == {"$ref": f"#/components/schemas/{schema_name}"}, (
        f"{method} {path}: expected $ref to {schema_name}, got {schema}"
    )
    assert schema_name in spec["components"]["schemas"]


def test_symbol_link_schema_requires_symbol_id(spec) -> None:
    schema = spec["components"]["schemas"]["SymbolLinkRequest"]
    assert schema["required"] == ["symbol_id"]
    assert schema["properties"]["symbol_id"]["type"] == "string"


def test_secret_collection_declares_metadata_response(spec) -> None:
    operation = spec["paths"]["/api/v1/secrets"]["get"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    response_schema_name = response_schema["$ref"].rsplit("/", maxsplit=1)[1]
    response_model = spec["components"]["schemas"][response_schema_name]
    data_schema = response_model["properties"]["data"]
    array_schema = next(schema for schema in data_schema["anyOf"] if schema.get("type") == "array")

    assert array_schema["items"] == {
        "$ref": "#/components/schemas/SecretMetadataResponse"
    }
    assert "value" not in spec["components"]["schemas"]["SecretMetadataResponse"]["properties"]


# ---------------------------------------------------------------------------
# affects: object contract behaviour
# ---------------------------------------------------------------------------


class _AffectsRepo:
    def __init__(self) -> None:
        self.linked: list[tuple[str, str]] = []
        self.unlinked: list[tuple[str, str]] = []

    def get_issue(self, issue_id: str):
        return {"id": issue_id} if issue_id == "i-1" else None

    def add_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        self.linked.append((issue_id, symbol_id))

    def remove_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        self.unlinked.append((issue_id, symbol_id))

    def get_affected_symbols(self, issue_id: str) -> list[str]:
        return ["sym-1"]


@pytest.fixture()
def env():
    repo = _AffectsRepo()
    return SimpleNamespace(client=TestClient(create_app(repository=repo)), repo=repo)


def test_affects_post_accepts_object_contract(env) -> None:
    resp = env.client.post("/api/v1/issues/i-1/affects", json={"symbol_id": "sym-9"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["symbol_id"] == "sym-9"
    assert env.repo.linked == [("i-1", "sym-9")]


def test_affects_delete_accepts_object_contract(env) -> None:
    resp = env.client.request(
        "DELETE", "/api/v1/issues/i-1/affects", json={"symbol_id": "sym-9"}
    )

    assert resp.status_code == 200, resp.text
    assert env.repo.unlinked == [("i-1", "sym-9")]


def test_affects_rejects_raw_string_body(env) -> None:
    resp = env.client.post("/api/v1/issues/i-1/affects", json="sym-9")

    assert resp.status_code == 422
    assert env.repo.linked == []


def test_affects_rejects_empty_object(env) -> None:
    resp = env.client.post("/api/v1/issues/i-1/affects", json={})

    assert resp.status_code == 422
    assert env.repo.linked == []


def test_affects_delete_rejects_raw_string_body(env) -> None:
    resp = env.client.request(
        "DELETE", "/api/v1/issues/i-1/affects", json="sym-9"
    )

    assert resp.status_code == 422
    assert env.repo.unlinked == []


def test_affects_object_body_still_404s_for_unknown_issue(env) -> None:
    resp = env.client.post("/api/v1/issues/missing/affects", json={"symbol_id": "sym-9"})

    assert resp.status_code == 404
    assert env.repo.linked == []


def test_epic_create_with_empty_object_keeps_current_behaviour() -> None:
    created: list = []

    class _Repo:
        def create_epic(self, epic) -> None:
            created.append(epic)

    client = TestClient(create_app(repository=_Repo()))
    resp = client.post("/api/v1/epics", json={})

    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    assert created == []
