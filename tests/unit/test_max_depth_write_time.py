"""Write-time policy validation: max_depth constraints and HARD violations (issue #532)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.application.actions import (
    PolicyViolationError,
    check_max_depth_at_write_time,
)
from socialseed_tasker.application.constraints import (
    Constraint,
    ConstraintCategory,
    ConstraintLevel,
    ConstraintStatus,
)
from socialseed_tasker.infrastructure.web_api.app import create_app

_UNIT_DIR = Path(__file__).resolve().parent


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


@pytest.fixture()
def component_id(client):
    resp = client.post(
        "/api/v1/components",
        json={"name": "Backend", "project": "test-project"},
    )
    return resp.json()["data"]["id"]


@pytest.fixture()
def make_issues(client, component_id):
    def _make(*titles: str) -> list[str]:
        ids = []
        for title in titles:
            resp = client.post(
                "/api/v1/issues",
                json={"title": title, "component_id": component_id},
            )
            ids.append(resp.json()["data"]["id"])
        return ids

    return _make


@pytest.fixture()
def policy_registry():
    from socialseed_tasker.infrastructure.web_api.routers.policy import _policy_engine

    yield _policy_engine
    _policy_engine["policies"] = []


def _max_depth_constraint(
    max_depth: int,
    level: ConstraintLevel = ConstraintLevel.HARD,
    status: ConstraintStatus = ConstraintStatus.ACTIVE,
) -> Constraint:
    return Constraint(
        category=ConstraintCategory.DEPENDENCIES,
        level=level,
        rule_type="max_depth",
        max_depth=max_depth,
        description=f"Max depth {max_depth}",
        status=status,
    )


class TestWriteTimeMaxDepthRule:
    def test_helper_raises_with_structured_fields(self, repo, client, make_issues):
        i1, i2, i3 = make_issues("depth one", "depth two", "depth three")
        resp = client.post(
            f"/api/v1/issues/{i2}/dependencies",
            json={"depends_on_id": i3},
        )
        assert resp.status_code == 201

        repo.create_constraint(_max_depth_constraint(1))

        with pytest.raises(PolicyViolationError) as excinfo:
            check_max_depth_at_write_time(repo, i1, i2)

        error = excinfo.value
        assert error.rule_type == "max_depth"
        assert error.constraint == "Max depth 1"
        assert error.severity == "hard"
        assert error.suggestion
        assert "exceeding max_depth 1" in error.message

    def test_helper_allows_depth_within_limit(self, repo, client, make_issues):
        i2, i3 = make_issues("within two", "within three")
        resp = client.post(
            f"/api/v1/issues/{i2}/dependencies",
            json={"depends_on_id": i3},
        )
        assert resp.status_code == 201

        repo.create_constraint(_max_depth_constraint(1))

        check_max_depth_at_write_time(repo, i2, i3)

    def test_helper_ignores_soft_constraints(self, repo, client, make_issues):
        i1, i2, i3 = make_issues("soft one", "soft two", "soft three")
        client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i3})
        repo.create_constraint(_max_depth_constraint(1, level=ConstraintLevel.SOFT))

        check_max_depth_at_write_time(repo, i1, i2)

    def test_helper_ignores_inactive_constraints(self, repo, client, make_issues):
        i1, i2, i3 = make_issues("inactive one", "inactive two", "inactive three")
        client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i3})
        repo.create_constraint(_max_depth_constraint(1, status=ConstraintStatus.INACTIVE))

        check_max_depth_at_write_time(repo, i1, i2)


class TestAddDependencyEndpoint:
    def test_dependency_exceeding_max_depth_returns_409(self, client, repo, make_issues):
        i1, i2, i3 = make_issues("api depth one", "api depth two", "api depth three")
        repo.create_constraint(_max_depth_constraint(1))

        ok = client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i3})
        assert ok.status_code == 201

        resp = client.post(f"/api/v1/issues/{i1}/dependencies", json={"depends_on_id": i2})
        assert resp.status_code == 409

        body = resp.json()
        assert body["error"]["code"] == "POLICY_VIOLATION"
        details = body["error"]["details"]
        assert details["rule_type"] == "max_depth"
        assert details["severity"] == "hard"
        assert details["constraint"] == "Max depth 1"
        assert details["message"]
        assert details["suggestion"]

        issue = client.get(f"/api/v1/issues/{i1}").json()["data"]
        assert issue["dependencies"] == []

    def test_dependency_within_max_depth_returns_201(self, client, repo, make_issues):
        i2, i3 = make_issues("api ok two", "api ok three")
        repo.create_constraint(_max_depth_constraint(1))

        resp = client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i3})
        assert resp.status_code == 201

    def test_soft_max_depth_does_not_block_write(self, client, repo, make_issues):
        i1, i2, i3 = make_issues("api soft one", "api soft two", "api soft three")
        repo.create_constraint(_max_depth_constraint(1, level=ConstraintLevel.SOFT))
        client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i3})

        resp = client.post(f"/api/v1/issues/{i1}/dependencies", json={"depends_on_id": i2})
        assert resp.status_code == 201

    def test_inactive_max_depth_does_not_block_write(self, client, repo, make_issues):
        i1, i2, i3 = make_issues("api inactive one", "api inactive two", "api inactive three")
        repo.create_constraint(_max_depth_constraint(1, status=ConstraintStatus.INACTIVE))
        client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i3})

        resp = client.post(f"/api/v1/issues/{i1}/dependencies", json={"depends_on_id": i2})
        assert resp.status_code == 201

    def test_bulk_dependency_exceeding_max_depth_returns_409(self, client, repo, make_issues):
        i1, i2, i3 = make_issues("bulk one", "bulk two", "bulk three")
        repo.create_constraint(_max_depth_constraint(1))
        client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i3})

        resp = client.post(
            f"/api/v1/issues/{i1}/dependencies/bulk",
            json={"depends_on_ids": [i2]},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "POLICY_VIOLATION"

        issue = client.get(f"/api/v1/issues/{i1}").json()["data"]
        assert issue["dependencies"] == []

    def test_circular_dependency_still_returns_409_with_message(self, client, make_issues):
        i1, i2 = make_issues("cycle one", "cycle two")
        first = client.post(f"/api/v1/issues/{i1}/dependencies", json={"depends_on_id": i2})
        assert first.status_code == 201

        resp = client.post(f"/api/v1/issues/{i2}/dependencies", json={"depends_on_id": i1})
        assert resp.status_code == 409

        body = resp.json()
        assert body["error"]["code"] == "CIRCULAR_DEPENDENCY"
        assert "cycle" in body["error"]["message"]
        assert isinstance(body["error"]["details"]["cycle_path"], list)


class TestPolicyViolationResponse:
    def _block_policy(self):
        from socialseed_tasker.application.policy import (
            Policy,
            PolicyRule,
            PolicyRuleType,
            PolicySeverity,
        )

        return Policy(
            name="Frontend never depends on backend",
            severity=PolicySeverity.BLOCKER,
            rules=[
                PolicyRule(
                    rule_type=PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY,
                    from_pattern="frontend",
                    to_pattern="backend",
                )
            ],
        )

    def _make_labeled_issues(self, client, component_id):
        labels = [["frontend"], ["backend"]]
        titles = ["labeled frontend issue", "labeled backend issue"]
        ids = []
        for title, issue_labels in zip(titles, labels, strict=True):
            resp = client.post(
                "/api/v1/issues",
                json={
                    "title": title,
                    "component_id": component_id,
                    "labels": issue_labels,
                },
            )
            ids.append(resp.json()["data"]["id"])
        return ids

    def test_policy_violation_in_block_mode_returns_409_structured(
        self, client, app, component_id, policy_registry
    ):
        policy = self._block_policy()
        policy_registry["policies"] = [policy]
        app.state.config.policy_enforcement_mode = "block"

        from_id, to_id = self._make_labeled_issues(client, component_id)
        resp = client.post(f"/api/v1/issues/{from_id}/dependencies", json={"depends_on_id": to_id})

        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "POLICY_VIOLATION"
        details = body["error"]["details"]
        assert details["policy_name"] == "Frontend never depends on backend"
        assert details["rule_type"] == "forbidden_label_dependency"
        assert details["severity"] == "hard"
        assert details["message"]
        assert details["suggestion"]

        issue = client.get(f"/api/v1/issues/{from_id}").json()["data"]
        assert issue["dependencies"] == []

    def test_policy_violation_in_warn_mode_allows_write(
        self, client, app, component_id, policy_registry
    ):
        policy_registry["policies"] = [self._block_policy()]
        app.state.config.policy_enforcement_mode = "warn"

        from_id, to_id = self._make_labeled_issues(client, component_id)
        resp = client.post(f"/api/v1/issues/{from_id}/dependencies", json={"depends_on_id": to_id})

        assert resp.status_code == 201
