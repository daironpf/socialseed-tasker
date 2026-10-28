import json
import os
import subprocess
import sys
import time
import urllib.request

import pytest
import yaml

pytestmark = [
    pytest.mark.integration,
    pytest.mark.self_contained,
]


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_provider_against_mock(tmp_path):
    _skip_if_not_integration()
    mock_port = os.getenv("TASKER_CONTRACT_MOCK_PORT", "9100")
    spec_path = tmp_path / "fixture-openapi.yaml"
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/health": {
                "get": {
                    "operationId": "health",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"}
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }
    with open(spec_path, "w", encoding="utf-8") as fh:
        yaml.dump(spec, fh)
    report_path = tmp_path / "report.json"
    proc = subprocess.Popen(
        [
            sys.executable,
            "tools/contracts/mockctl.py",
            "start",
            "--spec",
            str(spec_path),
            "--port",
            mock_port,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{mock_port}/health", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    else:
        raise AssertionError("mock server did not become reachable")
    try:
        subprocess.run(
            [
                sys.executable,
                "tools/contracts/contractctl.py",
                "run",
                "--provider",
                f"http://127.0.0.1:{mock_port}",
                "--spec",
                str(spec_path),
                "--out",
                str(report_path),
            ],
            check=True,
        )
        rep = json.loads(report_path.read_text())
        assert rep["overall"] is True
        assert len(rep["results"]) == 1
        assert rep["results"][0]["ok"] is True
    finally:
        proc.terminate()
