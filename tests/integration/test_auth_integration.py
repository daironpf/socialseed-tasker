import os
import json
import subprocess
import sys
import pytest

pytestmark = pytest.mark.integration

PY = sys.executable
MODULE = "-m"
MAIN = "socialseed_tasker.cli.main"

def run_cmd(args, env=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    proc = subprocess.run([PY, MODULE, MAIN] + args, capture_output=True, text=True, env=e)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def test_integration_cli_auth():
    users = {
        "admin": {"token": "admintoken123", "permissions": ["create:issue", "read:context", "read:impact", "add:dependency"]},
        "reader": {"token": "readertoken123", "permissions": ["read:context", "read:impact"]}
    }
    env = os.environ.copy()
    env["TASKER_AUTH_USERS"] = json.dumps(users)
    rc, out, err = run_cmd(["create-issue", "--id", "ia1", "--title", "IA1", "--token", "admintoken123"], env=env)
    assert rc == 0
    rc, out, err = run_cmd(["agent-context", "--issue-id", "ia1", "--token", "readertoken123"], env=env)
    assert rc == 0
    rc, out, err = run_cmd(["calculate-impact", "--issue-id", "ia1", "--token", "admintoken123"], env=env)
