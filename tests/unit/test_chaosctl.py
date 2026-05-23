from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_chaosctl():
    path = Path(__file__).resolve().parent.parent.parent / "tools" / "chaos" / "chaosctl.py"
    spec = importlib.util.spec_from_file_location("chaosctl", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["chaosctl"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def scenario_dir(tmp_path):
    d = tmp_path / "scenarios"
    d.mkdir(parents=True)
    (d / "test-scenario.yml").write_text("""
compose: docker-compose.chaos.yml
steps:
  - action: sleep
    seconds: 0.01
  - action: health_check
    service: api
    url: "http://localhost:8000/health"
    timeout: 1
    required: true
  - action: docker_compose
    compose: docker-compose.chaos.yml
    cmd: ps
  - action: exec
    cmd: "echo hello"
""")
    return d


@pytest.fixture
def chaosctl(scenario_dir):
    ctl = _load_chaosctl()
    ctl.SCENARIO_DIR = scenario_dir
    ctl.ARTIFACT_DIR = scenario_dir.parent / "artifacts"
    ctl.ARTIFACT_DIR.mkdir(exist_ok=True)
    return ctl


def test_list_scenarios(chaosctl):
    names = chaosctl.list_scenarios()
    assert "test-scenario" in names


def test_load_scenario(chaosctl):
    s = chaosctl.load_scenario("test-scenario")
    assert s["compose"] == "docker-compose.chaos.yml"
    assert len(s["steps"]) == 4


def test_run_scenario_success(chaosctl):
    with patch("chaosctl.run_cmd") as mock_run:
        mock_run.return_value.returncode = 0
        report, artifact = chaosctl.run_scenario("test-scenario")
    assert report["status"] == "success"
    assert len(report["actions"]) == 4
    assert len(report["checks"]) == 1
    assert report["checks"][0]["ok"] is True
    assert artifact.endswith(".json")
    assert Path(artifact).exists()


def test_run_scenario_health_fail(chaosctl, scenario_dir):
    import yaml
    path = scenario_dir / "test-scenario.yml"
    data = yaml.safe_load(path.read_text())
    # Add a required health check that will fail
    data["steps"] = [
        {"action": "health_check", "service": "api", "url": "http://localhost:8000/health",
         "timeout": 1, "required": True},
    ]
    path.write_text(yaml.dump(data))

    with patch("chaosctl.run_cmd") as mock_run:
        mock_run.return_value.returncode = 1
        report, artifact = chaosctl.run_scenario("test-scenario")
    assert report["status"] == "failed"
    assert len(report["errors"]) > 0


def test_run_scenario_unknown_action(chaosctl, scenario_dir):
    import yaml
    path = scenario_dir / "test-scenario.yml"
    data = yaml.safe_load(path.read_text())
    data["steps"].insert(0, {"action": "nonexistent"})
    path.write_text(yaml.dump(data))

    with patch("chaosctl.run_cmd"):
        report, artifact = chaosctl.run_scenario("test-scenario")
    assert report["status"] == "failed"
    assert "Unknown action" in report["errors"][0]


def test_scenario_not_found(chaosctl):
    with pytest.raises(FileNotFoundError):
        chaosctl.load_scenario("does-not-exist")


def test_status_no_artifacts(chaosctl, capsys):
    for f in chaosctl.ARTIFACT_DIR.glob("*"):
        f.unlink()
    chaosctl.status()
    out = capsys.readouterr().out
    assert "No artifacts" in out


def test_status_with_artifact(chaosctl, capsys):
    art = chaosctl.ARTIFACT_DIR / "test-20250101T000000Z.json"
    art.write_text(json.dumps({"status": "success"}))
    chaosctl.status()
    out = capsys.readouterr().out
    assert "test-20250101T000000Z.json" in out
    assert "success" in out


def test_record_artifact(chaosctl):
    report = {"scenario": "test", "status": "success"}
    path = chaosctl.record_artifact("test", report)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text())
    assert data["status"] == "success"
    assert data["scenario"] == "test"
