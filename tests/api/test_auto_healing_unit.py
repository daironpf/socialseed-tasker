"""Tests for the auto-healing pipeline engine and API (issue #520).

Covers the real execution flow (five stages, real patch artifact, real
issue creation), live cancel/restart semantics including fix reversion,
persistence across engine restarts, and the error paths (404/409).
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.domain.entities import Component, Issue, IssuePriority, IssueStatus
from socialseed_tasker.healing.engine import DEFAULT_HEALING_DIR, AutoHealingEngine
from socialseed_tasker.healing.storage import HealingStorage
from socialseed_tasker.infrastructure.web_api.app import create_app

COMPONENT_ID = uuid.uuid4()


class FakeRepo:
    """Minimal TaskRepositoryInterface stand-in backed by in-memory entities."""

    def __init__(self) -> None:
        self.anchor = Issue(
            title="Rate limiter crashes under load",
            description="Burst traffic triggers a crash in the rate limiter",
            labels=["rate-limit", "crash"],
            component_id=COMPONENT_ID,
            priority=IssuePriority.HIGH,
        )
        self.closed = Issue(
            title="Rate limiter missing burst protection",
            description="Closed after adding burst protection to the rate limiter",
            labels=["rate-limit"],
            component_id=COMPONENT_ID,
            status=IssueStatus.CLOSED,
            closed_at=datetime.now(timezone.utc),
        )
        self.created: list[Issue] = []

    def get_issue(self, issue_id: str) -> Issue | None:
        if issue_id == str(self.anchor.id):
            return self.anchor
        for issue in self.created:
            if str(issue.id) == issue_id:
                return issue
        return None

    def list_issues(self) -> list[Issue]:
        return [self.anchor, self.closed, *self.created]

    def get_component(self, component_id: str) -> Component:
        return Component(id=COMPONENT_ID, name="payments", project="system")

    def get_component_by_name(self, name: str, project: str = "system") -> Component:
        return Component(id=COMPONENT_ID, name=name, project=project)

    def find_issues_by_title(self, title: str, component_id: str) -> list[Issue]:
        return []

    def create_component(self, component: Component) -> Component:
        return component

    def create_issue(self, issue: Issue) -> Issue:
        self.created.append(issue)
        return issue

    def get_dependents(self, issue_id: str) -> list[Issue]:
        return []

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        return []


def _make_client(monkeypatch, tmp_path, stage_delay: str):
    monkeypatch.setenv("TASKER_HEALING_DIR", str(tmp_path / "heal"))
    monkeypatch.delenv("TASKER_HEALING_REPO", raising=False)
    monkeypatch.setenv("TASKER_HEALING_STAGE_DELAY", stage_delay)
    monkeypatch.delenv("TASKER_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("TASKER_API_KEY", raising=False)
    return TestClient(create_app(repository=FakeRepo()))


@pytest.fixture
def client(tmp_path, monkeypatch):
    with _make_client(monkeypatch, tmp_path, stage_delay="0") as test_client:
        yield test_client


@pytest.fixture
def slow_client(tmp_path, monkeypatch):
    with _make_client(monkeypatch, tmp_path, stage_delay="0.4") as test_client:
        yield test_client


def _start(client: TestClient, issue_id: str) -> dict:
    response = client.post("/api/v1/auto-healing/runs", json={"issueId": issue_id})
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _wait(client: TestClient, run_id: str, timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/v1/auto-healing/runs/{run_id}")
        if response.status_code == 429:  # token-bucket limiter caps the polling rate
            time.sleep(float(response.headers.get("Retry-After", "1")))
            continue
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        if data["status"] != "running":
            return data
        time.sleep(0.05)
    raise AssertionError("run did not settle in time")


def test_pipeline_completes_with_real_patch(client: TestClient):
    repo: FakeRepo = client.app.state.repository
    run = _start(client, str(repo.anchor.id))
    assert run["status"] == "running"
    assert len(run["stages"]) == 5
    assert all(stage["status"] == "pending" for stage in run["stages"])

    data = _wait(client, run["id"])
    assert data["status"] == "completed", data
    assert [stage["status"] for stage in data["stages"]] == ["completed"] * 5
    assert data["commitSha"]
    assert data["createdIssueId"]
    assert data["issueTitle"] == "Rate limiter crashes under load"
    assert len(data["logs"]) > 8

    # Stage 3 really persisted a fix issue through the repository.
    assert repo.created, "task_generation did not create an issue"
    assert repo.created[0].title.startswith("[Auto-Healing] Fix:")

    # Stage 4 produced exactly one real patch artifact.
    patches = client.get(f"/api/v1/auto-healing/runs/{run['id']}/patches").json()["data"]
    assert len(patches) == 1
    meta = patches[0]
    assert meta["stageId"] == "agent_fix"
    assert meta["strategy"] == "remove_debug_statements"
    assert "src/report.py" in meta["files"]
    assert meta["commitSha"] == data["commitSha"]
    assert meta["sizeBytes"] > 0

    # The download endpoint streams the raw unified diff as an attachment.
    download = client.get(f"/api/v1/auto-healing/runs/{run['id']}/patches/{meta['id']}")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("text/plain")
    assert "attachment" in download.headers["content-disposition"]
    content = download.text
    assert "--- a/src/report.py" in content
    assert '-    print("DEBUG: build_report started")' in content
    assert "-  console.log('DEBUG: total computed');" in content

    # The workspace file really changed on disk.
    workspace = client.app.state.auto_healing.workspace
    report = (workspace / "src" / "report.py").read_text(encoding="utf-8")
    assert 'print("DEBUG: build_report started")' not in report


def test_cancel_running_pipeline_and_restart(slow_client: TestClient):
    repo: FakeRepo = slow_client.app.state.repository
    run = _start(slow_client, str(repo.anchor.id))

    cancelled = slow_client.post(f"/api/v1/auto-healing/runs/{run['id']}/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["data"]["status"] == "cancelled"

    # Cancelling twice conflicts, and the run never completes on its own.
    assert slow_client.post(f"/api/v1/auto-healing/runs/{run['id']}/cancel").status_code == 409
    time.sleep(0.6)
    data = slow_client.get(f"/api/v1/auto-healing/runs/{run['id']}").json()["data"]
    assert data["status"] == "cancelled"

    # Restart resumes the cancelled run until completion.
    restarted = slow_client.post(f"/api/v1/auto-healing/runs/{run['id']}/restart")
    assert restarted.status_code == 200, restarted.text
    assert restarted.json()["data"]["status"] == "running"
    final = _wait(slow_client, run["id"])
    assert final["status"] == "completed"


def test_restart_while_running_conflicts(slow_client: TestClient):
    repo: FakeRepo = slow_client.app.state.repository
    run = _start(slow_client, str(repo.anchor.id))
    response = slow_client.post(f"/api/v1/auto-healing/runs/{run['id']}/restart")
    assert response.status_code == 409
    slow_client.post(f"/api/v1/auto-healing/runs/{run['id']}/cancel")


def test_restart_from_fix_stage_reverts_and_regenerates_patch(client: TestClient):
    repo: FakeRepo = client.app.state.repository
    run = _start(client, str(repo.anchor.id))
    completed = _wait(client, run["id"])
    assert completed["status"] == "completed"
    first_patch_id = completed["patches"][0]["id"]

    workspace = client.app.state.auto_healing.workspace
    fixed = (workspace / "src" / "report.py").read_text(encoding="utf-8")
    assert 'print("DEBUG: build_report started")' not in fixed

    response = client.post(
        f"/api/v1/auto-healing/runs/{run['id']}/restart",
        json={"stageId": "agent_fix"},
    )
    assert response.status_code == 200, response.text
    final = _wait(client, run["id"])
    assert final["status"] == "completed"
    assert [stage["status"] for stage in final["stages"]] == ["completed"] * 5

    # The old patch artifact was dropped and a fresh one generated.
    patch_ids = [meta["id"] for meta in final["patches"]]
    assert len(patch_ids) == 1
    assert patch_ids[0] != first_patch_id
    # Fix re-applied for real after the revert.
    report = (workspace / "src" / "report.py").read_text(encoding="utf-8")
    assert 'print("DEBUG: build_report started")' not in report


def test_missing_issue_and_unknown_run_return_404(client: TestClient):
    response = client.post("/api/v1/auto-healing/runs", json={"issueId": "no-such-issue"})
    assert response.status_code == 404

    assert client.get("/api/v1/auto-healing/runs/run-missing").status_code == 404
    assert client.get("/api/v1/auto-healing/runs/run-missing/logs").status_code == 404
    assert client.get("/api/v1/auto-healing/runs/run-missing/patches").status_code == 404
    assert client.post("/api/v1/auto-healing/runs/run-missing/cancel").status_code == 404
    assert client.post("/api/v1/auto-healing/runs/run-missing/restart").status_code == 404


def test_unknown_patch_and_stage_return_404_409(client: TestClient):
    repo: FakeRepo = client.app.state.repository
    run = _start(client, str(repo.anchor.id))
    final = _wait(client, run["id"])

    assert (
        client.get(f"/api/v1/auto-healing/runs/{run['id']}/patches/patch-nope").status_code == 404
    )
    assert (
        client.post(
            f"/api/v1/auto-healing/runs/{run['id']}/restart",
            json={"stageId": "not_a_stage"},
        ).status_code
        == 409
    )
    assert final["status"] == "completed"


def test_runs_persist_and_interrupted_runs_fail_on_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_HEALING_DIR", str(tmp_path / "persist"))
    monkeypatch.delenv("TASKER_HEALING_REPO", raising=False)
    storage = HealingStorage(tmp_path / "persist")

    interrupted = {
        "id": "run-interrupted",
        "issue_id": "iss-1",
        "issue_title": "From previous process",
        "repo": "workspace",
        "branch": "autohealing/run-interrupted",
        "commit_sha": "",
        "stages": [
            {"id": "test_failure", "label": "Test Failure Detected", "status": "completed"},
            {"id": "neo4j_root_cause", "label": "Root Cause", "status": "running"},
        ],
        "current_stage_index": 1,
        "started_at": "2026-09-27T10:00:00+00:00",
        "completed_at": None,
        "status": "running",
        "pr_url": None,
        "neo4j_node_id": None,
        "created_issue_id": None,
        "base_sha": None,
        "patches": [],
        "logs": [],
    }
    storage.save_runs([interrupted])

    engine = AutoHealingEngine(storage, repo_provider=lambda: None, stage_delay=0)
    reloaded = engine.get_run("run-interrupted")
    assert reloaded["status"] == "failed"
    assert reloaded["stages"][1]["status"] == "failed"
    assert reloaded["stages"][1]["details"] == "Interrupted by API restart"

    # Persisted runs survive a fresh engine instance.
    assert (storage.base_dir / "runs.json").exists()
    persisted = json.loads((storage.base_dir / "runs.json").read_text(encoding="utf-8"))
    assert persisted[0]["id"] == "run-interrupted"
    assert AutoHealingEngine(storage, repo_provider=lambda: None, stage_delay=0).list_runs()
