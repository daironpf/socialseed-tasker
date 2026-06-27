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

def _last_json_line(text: str) -> dict:
    """Extract the last JSON line from stderr (skipping log lines)."""
    for line in reversed(text.strip().splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return {}

def test_cli_unauthenticated_returns_error():
    code, out, err = run_cmd(["calculate-impact", "--issue-id", "x"])
    assert code == 2
    j = _last_json_line(err)
    assert j.get("status") == "error"
    assert "unauthenticated" in j.get("details", "") or "unauthenticated" in j.get("error", "")

def test_cli_forbidden_returns_error():
    """Using a token that doesn't match any known user returns error."""
    code, out, err = run_cmd(["create-issue", "--id", "x", "--title", "T", "--token", "invalid-token"])
    assert code == 2
    j = _last_json_line(err)
    assert j.get("status") == "error"
    assert "unauthenticated" in j.get("details", "") or "unauthenticated" in j.get("error", "")
