import json
import os
import subprocess
import time

import pytest
import yaml

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_provider_against_mock(tmp_path):
    _skip_if_not_integration()
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
            "python",
            "tools/contracts/mockctl.py",
            "start",
            "--spec",
            str(spec_path),
            "--port",
            "9100",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    try:
        subprocess.run(
            [
                "python",
                "tools/contracts/contractctl.py",
                "run",
                "--provider",
                "http://localhost:9100",
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
