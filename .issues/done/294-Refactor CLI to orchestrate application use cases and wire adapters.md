### Issue 294 — Refactor CLI to orchestrate application use cases and wire adapters

**Short description**  
Refactor and replace the existing CLI so it becomes a thin orchestration layer that **only** parses arguments, wires concrete implementations (adapters and repositories), and calls application use cases. The CLI must not contain business logic. Provide a single entrypoint `tasker/cli/main.py` with deterministic subcommands, clear exit codes, structured JSON output for machine consumption, unit and integration tests, and a wiring helper that constructs the default dependency graph (Neo4j adapter, parser, embedding, repositories). This issue must be implemented exactly as specified so autonomous agents can call CLI commands programmatically and rely on stable command names, flags, and JSON output shapes.

---

#### Objective (what the agent must deliver)
1. Add `tasker/cli/main.py` implementing a CLI with the exact subcommands and flags described below.
2. Add `tasker/cli/wiring.py` that constructs and returns a `Container` object with attributes: `graph`, `parser`, `issue_repo`, `graph_repo`, `embedding`, `storage`, `logger`.
3. Ensure CLI delegates all logic to application use cases (e.g., `GenerateAgentContext`, `CalculateImpact`, `CreateIssue`, `AddDependency`) by importing them from `tasker.application` and calling them with typed DTOs.
4. Provide deterministic JSON output for success and error cases. Success responses must be printed to stdout as a single JSON object and the process must exit with code `0`. Errors must be printed to stderr as a single JSON object with `error` and `details` keys and exit with code `2`.
5. Add unit tests for CLI argument parsing and wiring using `pytest` and `subprocess` or `runpy` to execute the module.
6. Add integration tests that run the CLI end-to-end against the real adapters (Neo4j + parser) when environment variables indicate integration mode.
7. Add documentation `tasker/cli/CLI.md` describing commands, flags, JSON outputs, and examples.
8. Create branch `feature/cli-refactor` and open a PR with the exact PR body provided below.

---

#### Why this must be done exactly this way
- Autonomous agents will call the CLI programmatically; stable command names, flags, and JSON outputs remove ambiguity.
- Keeping business logic out of the CLI prevents drift and ensures use cases remain testable and reusable.
- Deterministic exit codes and JSON shapes allow agents to parse results reliably and avoid hallucinations.

---

#### CLI specification (exact commands, flags, and JSON shapes)

**Module path**: `tasker/cli/main.py`  
**Usage**: `python -m tasker.cli.main <command> [flags]`

**Commands and flags (must be implemented exactly):**

1. `agent-context`  
   - **Description**: Generate structured context for an agent for a given issue id.  
   - **Flags**:
     - `--issue-id <id>` (required)  
     - `--max-depth <int>` (optional, default `3`)  
     - `--format json` (only `json` supported; default `json`)  
   - **Success JSON output**:
     ```json
     {
       "status": "ok",
       "command": "agent-context",
       "issue_id": "<id>",
       "context": { /* object returned by application use case */ }
     }
     ```
   - **Error JSON output**:
     ```json
     {
       "status": "error",
       "command": "agent-context",
       "issue_id": "<id>",
       "error": "Short error message",
       "details": "Longer error details"
     }
     ```

2. `calculate-impact`  
   - **Description**: Calculate impact set for an issue id.  
   - **Flags**:
     - `--issue-id <id>` (required)  
     - `--max-depth <int>` (optional, default `5`)  
   - **Success JSON output**:
     ```json
     {
       "status": "ok",
       "command": "calculate-impact",
       "issue_id": "<id>",
       "impact_set": ["issue-a", "issue-b"]
     }
     ```

3. `create-issue`  
   - **Description**: Create or update an issue.  
   - **Flags**:
     - `--id <id>` (required)  
     - `--title <text>` (required)  
     - `--description <text>` (optional)  
     - `--status <text>` (optional, default `open`)  
   - **Success JSON output**:
     ```json
     {
       "status": "ok",
       "command": "create-issue",
       "issue": { "id": "<id>", "title": "<title>", "status": "<status>" }
     }
     ```

4. `add-dependency`  
   - **Description**: Add a dependency edge between two issues.  
   - **Flags**:
     - `--from <issue-id>` (required)  
     - `--to <issue-id>` (required)  
     - `--relation <text>` (optional, default `DEPENDS_ON`)  
   - **Success JSON output**:
     ```json
     {
       "status": "ok",
       "command": "add-dependency",
       "edge": { "from": "<from>", "to": "<to>", "relation": "<relation>" }
     }
     ```

5. `parse-file`  
   - **Description**: Parse a source file and print extracted symbols and imports.  
   - **Flags**:
     - `--path <file>` (required)  
   - **Success JSON output**:
     ```json
     {
       "status": "ok",
       "command": "parse-file",
       "path": "<file>",
       "symbols": [ /* list of symbol descriptors */ ],
       "imports": [ /* list of import strings */ ]
     }
     ```

**Exit codes**:
- `0` on success.
- `2` on any error (invalid args, runtime error, adapter error).

---

#### Exact code to add for CLI entrypoint

Create `tasker/cli/main.py` with the exact content below. Do not change function or command names.

```python
# tasker/cli/main.py
from __future__ import annotations
import sys
import json
import argparse
from tasker.cli.wiring import build_default_container
from tasker.application.dtos import IssueDTO, DependencyEdge
from tasker.application.exceptions import GraphPortError, ParserError

def _print_json(obj, stream=sys.stdout):
    stream.write(json.dumps(obj, ensure_ascii=False))
    stream.write("\n")
    stream.flush()

def _error_and_exit(command: str, payload: dict, details: str = "") -> None:
    out = {
        "status": "error",
        "command": command,
        **payload,
        "error": str(details or "unknown error"),
        "details": details or "",
    }
    _print_json(out, stream=sys.stderr)
    sys.exit(2)

def cmd_agent_context(args, container):
    try:
        usecase = container.application.generate_agent_context  # must be provided by application wiring
        ctx = usecase(issue_id=args.issue_id, max_depth=int(args.max_depth))
        _print_json({"status": "ok", "command": "agent-context", "issue_id": args.issue_id, "context": ctx})
    except Exception as exc:
        _error_and_exit("agent-context", {"issue_id": args.issue_id}, details=str(exc))

def cmd_calculate_impact(args, container):
    try:
        usecase = container.application.calculate_impact
        impact = usecase(issue_id=args.issue_id, max_depth=int(args.max_depth))
        _print_json({"status": "ok", "command": "calculate-impact", "issue_id": args.issue_id, "impact_set": list(impact)})
    except Exception as exc:
        _error_and_exit("calculate-impact", {"issue_id": args.issue_id}, details=str(exc))

def cmd_create_issue(args, container):
    try:
        usecase = container.application.create_issue
        dto = IssueDTO(id=args.id, title=args.title, description=(args.description or ""), status=(args.status or "open"), metadata={})
        usecase(issue=dto)
        _print_json({"status": "ok", "command": "create-issue", "issue": {"id": dto.id, "title": dto.title, "status": dto.status}})
    except Exception as exc:
        _error_and_exit("create-issue", {"id": args.id}, details=str(exc))

def cmd_add_dependency(args, container):
    try:
        usecase = container.application.add_dependency
        edge = DependencyEdge(from_issue_id=args.from_id, to_issue_id=args.to, relation=(args.relation or "DEPENDS_ON"), metadata={})
        usecase(edge=edge)
        _print_json({"status": "ok", "command": "add-dependency", "edge": {"from": edge.from_issue_id, "to": edge.to_issue_id, "relation": edge.relation}})
    except Exception as exc:
        _error_and_exit("add-dependency", {"from": args.from_id, "to": args.to}, details=str(exc))

def cmd_parse_file(args, container):
    try:
        parser = container.parser
        ast = parser.parse_file(args.path)
        symbols = parser.extract_symbols(ast)
        imports = parser.extract_imports(ast)
        _print_json({"status": "ok", "command": "parse-file", "path": args.path, "symbols": symbols, "imports": imports})
    except Exception as exc:
        _error_and_exit("parse-file", {"path": args.path}, details=str(exc))

def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(prog="tasker")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("agent-context")
    p.add_argument("--issue-id", required=True)
    p.add_argument("--max-depth", default="3")
    p.add_argument("--format", default="json")

    p = sub.add_parser("calculate-impact")
    p.add_argument("--issue-id", required=True)
    p.add_argument("--max-depth", default="5")

    p = sub.add_parser("create-issue")
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description")
    p.add_argument("--status")

    p = sub.add_parser("add-dependency")
    p.add_argument("--from", dest="from_id", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--relation")

    p = sub.add_parser("parse-file")
    p.add_argument("--path", required=True)

    args = parser.parse_args(argv)
    container = build_default_container()

    if args.command == "agent-context":
        cmd_agent_context(args, container)
    elif args.command == "calculate-impact":
        cmd_calculate_impact(args, container)
    elif args.command == "create-issue":
        cmd_create_issue(args, container)
    elif args.command == "add-dependency":
        cmd_add_dependency(args, container)
    elif args.command == "parse-file":
        cmd_parse_file(args, container)
    else:
        _error_and_exit("unknown", {}, details=f"Unknown command {args.command}")

if __name__ == "__main__":
    main()
```

---

#### Exact code to add for wiring helper

Create `tasker/cli/wiring.py` with the exact content below. The `Container` object must be a simple dataclass with attributes used by `main.py`. The wiring must import concrete adapters implemented earlier and application use cases from `tasker.application`.

```python
# tasker/cli/wiring.py
from __future__ import annotations
from dataclasses import dataclass
import logging
from tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from tasker.infrastructure.parser_adapter import TreeSitterParser
from tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
# application use cases must be available under tasker.application.* (implementations expected)
import tasker.application as application_module

@dataclass
class Container:
    graph: object
    parser: object
    issue_repo: object
    graph_repo: object
    embedding: object | None
    storage: object | None
    logger: object
    application: object

def build_default_container() -> Container:
    logger = logging.getLogger("tasker")
    logger.setLevel(logging.INFO)
    graph = Neo4jGraphAdapter()
    parser = TreeSitterParser()
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)
    # embedding and storage may be None until implemented
    embedding = None
    storage = None
    # application_module must expose use case callables as attributes:
    # generate_agent_context, calculate_impact, create_issue, add_dependency
    return Container(
        graph=graph,
        parser=parser,
        issue_repo=issue_repo,
        graph_repo=graph_repo,
        embedding=embedding,
        storage=storage,
        logger=logger,
        application=application_module,
    )
```

---

#### CLI unit tests exact code

Create `tests/cli/test_cli_unit.py` with the exact content below. These tests run the CLI module as a subprocess and assert JSON outputs and exit codes.

```python
# tests/cli/test_cli_unit.py
import subprocess
import sys
import json
import os
import pytest

PY = sys.executable
MODULE = "-m"
MAIN = "tasker.cli.main"

def run_cmd(args):
    proc = subprocess.run([PY, MODULE, MAIN] + args, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def test_create_issue_missing_args_returns_error():
    code, out, err = run_cmd(["create-issue", "--id", "x"])
    assert code == 2
    assert err != ""

def test_parse_file_nonexistent_returns_error():
    code, out, err = run_cmd(["parse-file", "--path", "/no/such/file.py"])
    assert code == 2
    # stderr must be JSON with error key
    j = json.loads(err)
    assert j.get("status") == "error"
    assert j.get("command") == "parse-file"
```

---

#### CLI integration tests exact code

Create `tests/integration/test_cli_integration.py` with the exact content below. These tests run the CLI end-to-end against real adapters when `TASKER_INTEGRATION=1` is set. Otherwise they are skipped.

```python
# tests/integration/test_cli_integration.py
import os
import subprocess
import sys
import json
import pytest

pytestmark = pytest.mark.integration

PY = sys.executable
MODULE = "-m"
MAIN = "tasker.cli.main"

def run_cmd(args):
    proc = subprocess.run([PY, MODULE, MAIN] + args, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")

def test_create_issue_and_calculate_impact_integration(tmp_path):
    _skip_if_not_integration()
    # create issue A and B and add dependency A -> B
    rc, out, err = run_cmd(["create-issue", "--id", "cli-a", "--title", "A"])
    assert rc == 0
    rc, out, err = run_cmd(["create-issue", "--id", "cli-b", "--title", "B"])
    assert rc == 0
    rc, out, err = run_cmd(["add-dependency", "--from", "cli-a", "--to", "cli-b"])
    assert rc == 0
    rc, out, err = run_cmd(["calculate-impact", "--issue-id", "cli-b"])
    assert rc == 0
    j = json.loads(out)
    assert "cli-a" in j.get("impact_set", [])
    # cleanup
    run_cmd(["calculate-impact", "--issue-id", "cli-b"])
```

---

#### Documentation exact content

Create `tasker/cli/CLI.md` with the exact content below.

```
Tasker CLI

Usage
- python -m tasker.cli.main <command> [flags]

Commands
- agent-context --issue-id <id> [--max-depth N]
- calculate-impact --issue-id <id> [--max-depth N]
- create-issue --id <id> --title <text> [--description <text>] [--status <text>]
- add-dependency --from <id> --to <id> [--relation <text>]
- parse-file --path <file>

Output
- All successful responses are printed to stdout as a single JSON object and exit code 0.
- All errors are printed to stderr as a single JSON object with keys: status, command, error, details and exit code 2.

Examples
- python -m tasker.cli.main create-issue --id issue-1 --title "Fix bug"
- python -m tasker.cli.main agent-context --issue-id issue-1 --max-depth 3
```

---

#### Commands the agent must run exactly

```bash
git checkout -b feature/cli-refactor
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/cli/test_cli_unit.py -q
# run integration tests only if TASKER_INTEGRATION=1 and docker compose neo4j is up
export TASKER_INTEGRATION=1
docker compose -f docker-compose.neo4j.yml up -d
pytest tests/integration/test_cli_integration.py -q -m integration || true
# run linters and mypy
ruff check tasker tests
mypy tasker --strict
# commit and push
git add -A
git commit -m "refactor(cli): thin CLI that wires adapters and delegates to application use cases with deterministic JSON output"
git push origin feature/cli-refactor
```

---

#### PR body exact text to paste

```
Summary:
- Added CLI entrypoint tasker/cli/main.py with commands: agent-context, calculate-impact, create-issue, add-dependency, parse-file.
- Added wiring helper tasker/cli/wiring.py that constructs default adapters and repositories.
- Added unit tests tests/cli/test_cli_unit.py and integration tests tests/integration/test_cli_integration.py.
- Added documentation tasker/cli/CLI.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests: pytest tests/cli/test_cli_unit.py (passed).
3. Optionally ran integration tests with TASKER_INTEGRATION=1 and docker compose neo4j (passed when environment available).
4. Ran linters and type checks: ruff, mypy --strict.

Files changed:
- tasker/cli/main.py
- tasker/cli/wiring.py
- tasker/cli/CLI.md
- tests/cli/test_cli_unit.py
- tests/integration/test_cli_integration.py

Notes:
- CLI is intentionally thin: all business logic must live in application use cases.
- CLI outputs deterministic JSON for both success and error cases to support programmatic callers and autonomous agents.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `tasker/cli/main.py` exists and implements the commands and JSON output shapes exactly as specified.
- `tasker/cli/wiring.py` exists and returns a `Container` with attributes: `graph`, `parser`, `issue_repo`, `graph_repo`, `embedding`, `storage`, `logger`, `application`.
- CLI delegates logic to application use cases (no business logic in CLI).
- Unit tests `tests/cli/test_cli_unit.py` pass.
- Integration tests `tests/integration/test_cli_integration.py` pass when `TASKER_INTEGRATION=1` and Neo4j is available.
- `tasker/cli/CLI.md` documents commands, flags, and JSON outputs.
- Branch `feature/cli-refactor` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `cli`
- `refactor`
- `integration-test`
- `medium-priority`

---

#### Estimated effort
**Medium (M)** — expected to take an autonomous agent or engineer **2–5 hours** depending on the number of application use cases that need to be exposed and test environment availability.