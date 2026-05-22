### Issue 295 — Implement domain use cases GenerateAgentContext and CalculateImpact and add domain unit and integration tests

**Short description**  
Implement two canonical application use cases **`GenerateAgentContext`** and **`CalculateImpact`** inside the application layer. Both must be deterministic, fully typed, and depend only on the application ports and repository protocols. Add comprehensive unit tests for domain logic and integration tests that exercise the full stack (parser + Neo4j repositories + adapter) using the existing Docker Compose Neo4j service. All code, tests, and documentation must be explicit and unambiguous so an autonomous agent can implement, run, and verify them without guessing.

---

### Objective what the agent must deliver
1. Add `tasker/application/use_cases.py` containing two functions (or callables) with exact names and signatures:
   - `def generate_agent_context(issue_id: str, max_depth: int, graph_repo: GraphRepository, issue_repo: IssueRepository, parser: ParserPort) -> dict[str, Any]`
   - `def calculate_impact(issue_id: str, max_depth: int, graph_repo: GraphRepository) -> list[str]`
2. Implement deterministic logic:
   - **`calculate_impact`** returns a list of issue ids that transitively depend on `issue_id` up to `max_depth` using `GraphRepository.find_impact_set`.
   - **`generate_agent_context`** returns a JSON-serializable dict containing:
     - **`issue`**: IssueDTO for `issue_id` (from `IssueRepository.get`)
     - **`impact_set`**: list of impacted issue ids (from `calculate_impact`)
     - **`related_code`**: for each impacted issue id and the original issue, a list of parsed symbols and imports for files referenced in issue metadata under key `"files"` (use `ParserPort.parse_file`, `extract_symbols`, `extract_imports`). If `files` is absent, skip.
     - **`reasoning`**: a deterministic trace list of steps the use case executed (strings) to provide explainability.
3. Add unit tests for both use cases that mock `GraphRepository`, `IssueRepository`, and `ParserPort` to validate behavior and error handling.
4. Add integration tests that wire the real Neo4j repositories and parser adapter to validate end-to-end behavior:
   - Use `docker-compose.neo4j.yml` to start Neo4j.
   - Create sample issues and dependencies, add sample files in a temporary repo, run `generate_agent_context` and `calculate_impact`, and assert expected shapes and values.
5. Add documentation `tasker/application/USE_CASES.md` describing inputs, outputs, reasoning trace format, and examples.
6. Create branch `feature/use-cases-impact-context` and open a PR with the exact PR body provided below.

---

### Files to add or modify exact paths
- `tasker/application/use_cases.py` **(new)**
- `tasker/application/USE_CASES.md` **(new)**
- `tests/application/test_use_cases_unit.py` **(new)**
- `tests/integration/test_use_cases_integration.py` **(new)**
- Update `tasker/application/__init__.py` to export `generate_agent_context` and `calculate_impact` if present.

---

### Exact code to add for use cases

Create `tasker/application/use_cases.py` with the exact content below. Do not change function names or signatures.

```python
# tasker/application/use_cases.py
from __future__ import annotations
from typing import Any, Dict, List
from tasker.application.repositories import GraphRepository, IssueRepository
from tasker.application.ports import ParserPort
from tasker.application.dtos import IssueDTO
from tasker.application.exceptions import GraphPortError, ParserError

def calculate_impact(issue_id: str, max_depth: int, graph_repo: GraphRepository) -> List[str]:
    """
    Deterministic impact calculation.

    - Calls graph_repo.find_impact_set(issue_id, max_depth)
    - Returns a sorted list of unique issue ids (sorted for determinism)
    - Raises GraphPortError on repository failures
    """
    try:
        impacted = list(graph_repo.find_impact_set(issue_id, max_depth))
        # Ensure deterministic ordering and uniqueness
        unique = sorted(set(impacted))
        return unique
    except Exception as exc:
        raise GraphPortError(f"calculate_impact failed for {issue_id}: {exc}") from exc

def generate_agent_context(
    issue_id: str,
    max_depth: int,
    graph_repo: GraphRepository,
    issue_repo: IssueRepository,
    parser: ParserPort,
) -> Dict[str, Any]:
    """
    Generate structured context for an agent.

    Output shape:
    {
      "issue": { IssueDTO as dict or None },
      "impact_set": [ "issue-a", ... ],
      "related_code": {
         "<issue-id>": {
             "files": {
                 "<path>": { "symbols": [...], "imports": [...] }
             }
         }
      },
      "reasoning": [ "step 1", "step 2", ... ]
    }
    """
    reasoning: List[str] = []
    try:
        reasoning.append(f"Start context generation for issue {issue_id} with max_depth={max_depth}")
        # Load primary issue
        issue = issue_repo.get(issue_id)
        reasoning.append(f"Loaded issue {issue_id}: {'found' if issue else 'missing'}")
        # Compute impact set
        impact = calculate_impact(issue_id, max_depth, graph_repo)
        reasoning.append(f"Calculated impact set of size {len(impact)}")
        # Build related_code by inspecting issue metadata for file lists
        related_code: Dict[str, Any] = {}
        # include original issue in the set to gather its files too
        all_ids = [issue_id] + [i for i in impact if i != issue_id]
        for iid in all_ids:
            try:
                reasoning.append(f"Fetching issue data for {iid}")
                iobj = issue_repo.get(iid)
                if iobj is None:
                    reasoning.append(f"Issue {iid} not found; skipping files")
                    continue
                files = []
                # Expect metadata to be mapping and may contain "files": list[str]
                try:
                    files = list(iobj.metadata.get("files", [])) if getattr(iobj, "metadata", None) else []
                except Exception:
                    files = []
                if not files:
                    reasoning.append(f"No files listed for {iid}")
                    continue
                related_code[iid] = {"files": {}}
                for path in files:
                    try:
                        reasoning.append(f"Parsing file {path} for issue {iid}")
                        ast = parser.parse_file(path)
                        symbols = parser.extract_symbols(ast)
                        imports = parser.extract_imports(ast)
                        related_code[iid]["files"][path] = {"symbols": symbols, "imports": imports}
                        reasoning.append(f"Parsed file {path}: symbols={len(symbols)}, imports={len(imports)}")
                    except ParserError as pexc:
                        reasoning.append(f"ParserError for {path}: {pexc}")
                    except Exception as exc:
                        reasoning.append(f"Unexpected parser error for {path}: {exc}")
            except Exception as exc:
                reasoning.append(f"Failed to fetch or process issue {iid}: {exc}")
        # Serialize issue DTO to dict if present
        issue_dict = None
        if issue is not None:
            issue_dict = {
                "id": issue.id,
                "title": issue.title,
                "description": issue.description,
                "status": issue.status,
                "metadata": dict(issue.metadata or {}),
            }
        reasoning.append("Context generation completed")
        return {
            "issue": issue_dict,
            "impact_set": impact,
            "related_code": related_code,
            "reasoning": reasoning,
        }
    except Exception as exc:
        reasoning.append(f"generate_agent_context failed: {exc}")
        raise GraphPortError(f"generate_agent_context failed for {issue_id}: {exc}") from exc
```

---

### Exact unit tests to add

Create `tests/application/test_use_cases_unit.py` with the exact content below.

```python
# tests/application/test_use_cases_unit.py
from unittest.mock import MagicMock
import pytest
from tasker.application.use_cases import calculate_impact, generate_agent_context
from tasker.application.dtos import IssueDTO

def make_issue(id: str, files=None):
    return IssueDTO(id=id, title=f"Title {id}", description="", status="open", metadata={"files": files or []})

def test_calculate_impact_calls_graph_repo_and_returns_sorted_unique():
    graph_repo = MagicMock()
    graph_repo.find_impact_set.return_value = ["b", "a", "b"]
    res = calculate_impact("x", max_depth=3, graph_repo=graph_repo)
    assert res == ["a", "b"]

def test_generate_agent_context_includes_issue_and_related_code_and_reasoning():
    graph_repo = MagicMock()
    issue_repo = MagicMock()
    parser = MagicMock()

    # Setup graph impact
    graph_repo.find_impact_set.return_value = ["imp-1"]
    # Setup issues
    issue_repo.get.side_effect = lambda iid: make_issue(iid, files=["/tmp/f1.py"]) if iid in ("root", "imp-1") else None
    # Parser returns simple AST and symbols/imports
    parser.parse_file.return_value = {"type": "root", "children": []}
    parser.extract_symbols.return_value = [{"name": "f", "type": "function"}]
    parser.extract_imports.return_value = ["os"]

    ctx = generate_agent_context("root", max_depth=2, graph_repo=graph_repo, issue_repo=issue_repo, parser=parser)
    assert "issue" in ctx
    assert "impact_set" in ctx and ctx["impact_set"] == ["imp-1"]
    assert "related_code" in ctx and "imp-1" in ctx["related_code"]
    assert isinstance(ctx["reasoning"], list)
```

---

### Exact integration test to add

Create `tests/integration/test_use_cases_integration.py` with the exact content below. This test requires Neo4j running and uses the real Neo4j repositories and parser adapter. It will be marked integration.

```python
# tests/integration/test_use_cases_integration.py
import os
import tempfile
import textwrap
import pytest
from tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from tasker.infrastructure.parser_adapter import TreeSitterParser
from tasker.application.use_cases import generate_agent_context, calculate_impact
from tasker.application.dtos import IssueDTO, DependencyEdge

pytestmark = pytest.mark.integration

NEO4J_URI = os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("TASKER_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("TASKER_NEO4J_PASSWORD", "test")

PY_SIMPLE = textwrap.dedent("""
def f():
    return 1
""")

def test_generate_agent_context_end_to_end(tmp_path):
    # Start real adapters
    graph = Neo4jGraphAdapter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)
    parser = TreeSitterParser()

    # Create sample file
    fpath = tmp_path / "f.py"
    fpath.write_text(PY_SIMPLE, encoding="utf-8")

    # Create issues and dependency
    a = IssueDTO(id="issue-a", title="A", description="", status="open", metadata={"files": [str(fpath)]})
    b = IssueDTO(id="issue-b", title="B", description="", status="open", metadata={})
    issue_repo.save(a)
    issue_repo.save(b)
    edge = DependencyEdge(from_issue_id="issue-a", to_issue_id="issue-b", relation="DEPENDS_ON", metadata={})
    graph_repo.add_dependency(edge)

    # Run use cases
    impact = calculate_impact("issue-b", max_depth=3, graph_repo=graph_repo)
    assert "issue-a" in impact

    ctx = generate_agent_context("issue-b", max_depth=3, graph_repo=graph_repo, issue_repo=issue_repo, parser=parser)
    assert ctx["issue"] is not None
    assert "issue-a" in ctx["impact_set"]
    # related_code should include issue-a and the parsed file
    assert "issue-a" in ctx["related_code"]
    assert str(fpath) in ctx["related_code"]["issue-a"]["files"]

    # cleanup
    issue_repo.delete("issue-a")
    issue_repo.delete("issue-b")
    graph.close()
```

---

### Exact documentation to add

Create `tasker/application/USE_CASES.md` with the exact content below.

```
Use Cases GenerateAgentContext and CalculateImpact

Purpose
- calculate_impact(issue_id, max_depth, graph_repo) -> list[str]
  Deterministically returns sorted unique impacted issue ids.

- generate_agent_context(issue_id, max_depth, graph_repo, issue_repo, parser) -> dict
  Returns a JSON-serializable dict with keys:
    - issue: IssueDTO serialized as dict or null
    - impact_set: list of issue ids
    - related_code: mapping issue_id -> { files: { path: { symbols: [...], imports: [...] } } }
    - reasoning: list[str] deterministic trace of steps executed

Reasoning trace
- The reasoning list contains short deterministic messages describing each step.
- Use cases must append messages for start, load issue, calculate impact, parse files, and completion.

Examples
- calculate_impact("issue-b", 3, graph_repo)
- generate_agent_context("issue-b", 3, graph_repo, issue_repo, parser)
```

---

### Commands the agent must run exactly

```bash
git checkout -b feature/use-cases-impact-context
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/application/test_use_cases_unit.py -q
# start neo4j for integration tests if needed
docker compose -f docker-compose.neo4j.yml up -d
# run integration tests (tagged)
pytest tests/integration/test_use_cases_integration.py -q -m integration
# run linters and mypy
ruff check tasker tests
mypy tasker --strict
# commit and push
git add -A
git commit -m "feat(app): add generate_agent_context and calculate_impact use cases with unit and integration tests"
git push origin feature/use-cases-impact-context
```

---

### PR body exact text to paste

```
Summary:
- Added tasker/application/use_cases.py with deterministic implementations of calculate_impact and generate_agent_context.
- Added documentation tasker/application/USE_CASES.md describing inputs, outputs, and reasoning trace.
- Added unit tests tests/application/test_use_cases_unit.py.
- Added integration tests tests/integration/test_use_cases_integration.py that exercise Neo4j repositories and parser adapter.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests: pytest tests/application/test_use_cases_unit.py (passed).
3. Started Neo4j via docker compose: docker compose -f docker-compose.neo4j.yml up -d
4. Ran integration tests: pytest tests/integration/test_use_cases_integration.py -m integration (passed).
5. Ran linters and type checks: ruff, mypy --strict.

Files changed:
- tasker/application/use_cases.py
- tasker/application/USE_CASES.md
- tests/application/test_use_cases_unit.py
- tests/integration/test_use_cases_integration.py

Notes:
- generate_agent_context produces a deterministic reasoning trace to support explainability for agents.
- calculate_impact returns a sorted unique list for deterministic downstream behavior.
```

---

### Acceptance criteria must be satisfied exactly
- `tasker/application/use_cases.py` exists and contains `calculate_impact` and `generate_agent_context` with the exact function names and signatures specified.
- Unit tests `tests/application/test_use_cases_unit.py` pass.
- Integration test `tests/integration/test_use_cases_integration.py` passes when Neo4j is available via `docker-compose.neo4j.yml`.
- `tasker/application/USE_CASES.md` documents the use cases, output shapes, and reasoning trace format.
- Branch `feature/use-cases-impact-context` created and PR opened with the exact PR body above.

---

### Labels to apply on GitHub
- `application`
- `domain`
- `tests`
- `medium-priority`

---

### Estimated effort
**Medium (M)** — expected to take an autonomous agent or engineer **2–5 hours** depending on test environment and Neo4j availability.