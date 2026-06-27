#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
EXAMPLE_A = ROOT / "a.py"
EXAMPLE_B = ROOT / "b.py"
OUTPUT = ROOT.parent / "output.json"

PY = sys.executable
MODULE = "-m"
MAIN = "socialseed_tasker.cli.main"


def run_cmd(args):
    proc = subprocess.run([PY, MODULE, MAIN] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        print("Command failed:", args, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        sys.exit(proc.returncode)
    return proc.stdout


def create_issue(issue_id, title, files):
    run_cmd(["create-issue", "--id", issue_id, "--title", title])
    try:
        from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
        from socialseed_tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
        from socialseed_tasker.application.dtos import IssueDTO

        graph = Neo4jGraphAdapter(
            uri=os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("TASKER_NEO4J_USER", "neo4j"),
            password=os.getenv("TASKER_NEO4J_PASSWORD", "test"),
        )
        repo = Neo4jIssueRepository(graph)
        dto = IssueDTO(id=issue_id, title=title, description="", status="open", metadata={"files": files})
        repo.save(dto)
        graph.close()
    except Exception as exc:
        print("Warning: could not update metadata via repository, continuing. Error:", exc, file=sys.stderr)


def add_dependency(from_id, to_id):
    run_cmd(["add-dependency", "--from", from_id, "--to", to_id])


def generate_context(issue_id):
    out = run_cmd(["agent-context", "--issue-id", issue_id, "--max-depth", "3"])
    j = json.loads(out)
    return j


def main():
    create_issue("example-a", "Example A", [str(EXAMPLE_A)])
    create_issue("example-b", "Example B", [str(EXAMPLE_B)])
    add_dependency("example-a", "example-b")
    ctx = generate_context("example-b")
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        json.dump(ctx, fh, indent=2)
    print("Wrote example output to", OUTPUT)


if __name__ == "__main__":
    main()
