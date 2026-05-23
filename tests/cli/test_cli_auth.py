import subprocess
import sys
import json
import os

PY = sys.executable
MODULE = "-m"
MAIN = "socialseed_tasker.cli.main"

def run_cmd(args, env=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    proc = subprocess.run([PY, MODULE, MAIN] + args, capture_output=True, text=True, env=e)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def test_cli_unauthenticated_returns_error():
    code, out, err = run_cmd(["calculate-impact", "--issue-id", "x"])
    assert code == 2
    j = json.loads(err)
    assert j.get("status") == "error"
    assert "unauthenticated" in j.get("details", "") or "unauthenticated" in j.get("error", "")

def test_cli_forbidden_returns_error():
    users = {
        "reader": {"token": "rt", "permissions": ["read:context"]}
    }
    env = os.environ.copy()
    env["TASKER_AUTH_USERS"] = json.dumps(users)
    code, out, err = run_cmd(["create-issue", "--id", "x", "--title", "T", "--token", "rt"], env=env)
    assert code == 2
    j = json.loads(err)
    assert j.get("status") == "error"
    assert "forbidden" in j.get("details", "") or "forbidden" in j.get("error", "")
