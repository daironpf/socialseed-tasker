"""POST /issues never dies with the data-quality pipeline (issue #593 follow-up).

The dq factory raised ``NotImplementedError`` for any rule kind it did not
know, and the production Redis carried ``rule-593-live`` with
``kind="not_empty"`` — so every valid issue create turned into a 500.
Two defence layers are covered here:

1. The pipeline skips rules with unsupported kinds instead of instantiating
   a bare ``BaseRule`` that explodes on ``validate()``.
2. The web route tolerates dq failures (pre/post-ingest are best-effort).

The happy path with a live ``not_empty`` rule — the exact production shape —
must yield 201.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app

_UNIT_DIR = Path(__file__).resolve().parents[1] / "unit"


@pytest.fixture()
def client() -> TestClient:
    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    return TestClient(create_app(repository=MockRepository()))


def _create_component(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/components",
        json={"name": "Backend", "project": "test-project"},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["data"]["id"]


def _patch_pipeline(monkeypatch: pytest.MonkeyPatch, pipeline) -> None:
    monkeypatch.setattr(
        "socialseed_tasker.cli.wiring.build_default_container",
        lambda: SimpleNamespace(data_quality_pipeline=pipeline),
    )


class _ExplodingPipeline:
    def run_pre_ingest(self, record, record_id=None):
        raise NotImplementedError("unsupported rule kind")

    def run_post_ingest(self, record, record_id=None):
        raise NotImplementedError("unsupported rule kind")


def _pipeline_with_rule(kind: str):
    from socialseed_tasker.data_quality.pipeline import DataQualityPipeline
    from socialseed_tasker.data_quality.rules import RuleRegistry
    from socialseed_tasker.events.bus import EventBus
    from socialseed_tasker.infrastructure.memory_storage import MemoryStorage

    storage = MemoryStorage()
    registry = RuleRegistry(storage)
    registry.add(
        {"id": "rule-live", "name": "title not empty", "kind": kind, "target": "title"}
    )
    return DataQualityPipeline(storage, registry, EventBus())


def test_create_issue_survives_broken_dq_pipeline(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pipeline(monkeypatch, _ExplodingPipeline())
    payload = {"title": "Issue dq guard", "component_id": _create_component(client)}
    resp = client.post("/api/v1/issues", json=payload)
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["title"] == "Issue dq guard"


def test_create_issue_with_live_not_empty_rule(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pipeline(monkeypatch, _pipeline_with_rule("not_empty"))
    payload = {"title": "Issue with live rule", "component_id": _create_component(client)}
    resp = client.post("/api/v1/issues", json=payload)
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["title"] == "Issue with live rule"


def test_create_issue_skips_unsupported_kind_rule(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pipeline(monkeypatch, _pipeline_with_rule("bogus_kind"))
    payload = {"title": "Issue bogus rule", "component_id": _create_component(client)}
    resp = client.post("/api/v1/issues", json=payload)
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["title"] == "Issue bogus rule"
