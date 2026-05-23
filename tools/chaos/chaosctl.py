#!/usr/bin/env python3
# tools/chaos/chaosctl.py
from __future__ import annotations
import argparse
import subprocess
import sys
import time
import json
from pathlib import Path
import datetime
import yaml

ROOT = Path(__file__).resolve().parent
SCENARIO_DIR = ROOT / "scenarios"
ARTIFACT_DIR = ROOT / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd, check=True, capture=False, env=None):
    res = subprocess.run(cmd, shell=True, check=False, capture_output=capture, env=env, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nstdout:{res.stdout}\nstderr:{res.stderr}")
    return res

def load_scenario(name: str):
    path = SCENARIO_DIR / f"{name}.yml"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {name}")
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def record_artifact(name: str, report: dict):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ARTIFACT_DIR / f"{name}-{ts}.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("Wrote artifact", out)
    return str(out)

def run_scenario(name: str):
    scenario = load_scenario(name)
    report = {"scenario": name, "start": time.time(), "actions": [], "checks": [], "errors": []}
    try:
        for step in scenario.get("steps", []):
            action = step.get("action")
            report["actions"].append({"action": action, "params": step})
            if action == "docker_compose":
                cmd = f"docker compose -f {step['compose']} {step['cmd']}"
                run_cmd(cmd)
            elif action == "exec":
                cmd = f"docker compose -f {scenario.get('compose','docker-compose.chaos.yml')} exec -T chaos-agent {step['cmd']}"
                run_cmd(cmd)
            elif action == "sleep":
                time.sleep(float(step.get("seconds", 1)))
            elif action == "health_check":
                svc = step["service"]
                url = step["url"]
                timeout = int(step.get("timeout", 30))
                ok = False
                start = time.time()
                while time.time() - start < timeout:
                    try:
                        r = run_cmd(f"curl -sSf {url}", check=False, capture=True)
                        if r.returncode == 0:
                            ok = True
                            break
                    except Exception:
                        pass
                    time.sleep(1)
                report["checks"].append({"service": svc, "url": url, "ok": ok})
                if not ok and step.get("required", True):
                    raise RuntimeError(f"Health check failed for {svc}")
            else:
                raise RuntimeError(f"Unknown action {action}")
        report["end"] = time.time()
        report["status"] = "success"
    except Exception as exc:
        report["end"] = time.time()
        report["status"] = "failed"
        report["errors"].append(str(exc))
    artifact = record_artifact(name, report)
    return report, artifact

def list_scenarios():
    return [p.stem for p in SCENARIO_DIR.glob("*.yml")]

def status():
    arts = sorted(ARTIFACT_DIR.glob("*.json"), reverse=True)
    if not arts:
        print("No artifacts")
        return
    latest = arts[0]
    print("Latest artifact:", latest)
    print(latest.read_text())

def main():
    p = argparse.ArgumentParser(prog="chaosctl")
    sub = p.add_subparsers(dest="cmd")
    run = sub.add_parser("run")
    run.add_argument("scenario")
    sub.add_parser("list")
    sub.add_parser("status")
    args = p.parse_args()
    if args.cmd == "run":
        print("Running scenario", args.scenario)
        r, a = run_scenario(args.scenario)
        print("Result:", r["status"])
        sys.exit(0 if r["status"] == "success" else 2)
    elif args.cmd == "list":
        for s in list_scenarios():
            print(s)
    elif args.cmd == "status":
        status()
    else:
        p.print_help()

if __name__ == "__main__":
    main()
