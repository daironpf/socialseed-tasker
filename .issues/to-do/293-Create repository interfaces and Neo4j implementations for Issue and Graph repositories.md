### Issue 293 — Create repository interfaces and Neo4j implementations for Issue and Graph repositories

**Short description**  
Define clear repository interfaces (contracts) for domain persistence and graph queries, then implement concrete Neo4j-backed adapters that implement those interfaces. The goal is to provide deterministic, typed repository APIs that the application layer calls, and to wire them to the `Neo4jGraphAdapter` so autonomous agents can persist and query domain entities without guessing method names, return shapes, or error semantics.

---

#### Objective (what the agent must deliver)
1. Add a canonical repository interface module at `tasker/application/repositories.py` that defines `IssueRepository` and `GraphRepository` as `Protocol` types with full typing, docstrings, and expected exceptions.
2. Add domain DTOs used by repositories in `tasker/application/dtos.py` (immutable dataclasses): `IssueDTO`, `IssueSummary`, `DependencyEdge`.
3. Implement Neo4j-backed repository classes:
   - `tasker/infrastructure/neo4j_issue_repository.py` implementing `IssueRepository`.
   - `tasker/infrastructure/neo4j_graph_repository.py` implementing `GraphRepository`.
   Both must use `tasker.infrastructure.neo4j_adapter.Neo4jGraphAdapter` (the adapter implemented earlier) and must not leak Neo4j driver types into the application layer.
4. Add unit tests for both repository implementations that mock `Neo4jGraphAdapter` and verify method behavior, return shapes, and error mapping.
5. Add integration tests that exercise basic flows against a running Neo4j instance (use `docker-compose.neo4j.yml`).
6. Add documentation `tasker/application/REPOSITORIES.md` describing the contracts, example usage, and expected Cypher patterns used by the Neo4j implementations.
7. Create branch `feature/repositories-neo4j` and open a PR with the exact PR body provided below.

---

#### Why this must be done exactly this way
- Application code must depend on stable repository contracts, not on driver APIs.
- Autonomous agents will implement or mock repositories based on these exact Protocols.
- Neo4j implementations must be testable and replaceable without changing application code.

---

#### Files to add or modify (exact paths)
- `tasker/application/repositories.py` **(new)**
- `tasker/application/dtos.py` **(new)**
- `tasker/application/REPOSITORIES.md` **(new)**
- `tasker/infrastructure/neo4j_issue_repository.py` **(new)**
- `tasker/infrastructure/neo4j_graph_repository.py` **(new)**
- `tests/infrastructure/test_neo4j_issue_repository_unit.py` **(new)**
- `tests/infrastructure/test_neo4j_graph_repository_unit.py` **(new)**
- `tests/integration/test_repositories_integration.py` **(new)**
- Update `tasker/infrastructure/__init__.py` to export the new repository classes.

---

#### Exact code to add for repository interfaces and DTOs

Create `tasker/application/dtos.py` with the exact content below.

```python
# tasker/application/dtos.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any, Optional

@dataclass(frozen=True)
class IssueDTO:
    id: str
    title: str
    description: str
    status: str
    metadata: Mapping[str, Any]

@dataclass(frozen=True)
class IssueSummary:
    id: str
    title: str
    status: str

@dataclass(frozen=True)
class DependencyEdge:
    from_issue_id: str
    to_issue_id: str
    relation: str
    metadata: Optional[Mapping[str, Any]] = None
```

Create `tasker/application/repositories.py` with the exact content below.

```python
# tasker/application/repositories.py
from __future__ import annotations
from typing import Protocol, Iterable, Optional
from tasker.application.dtos import IssueDTO, IssueSummary, DependencyEdge
from tasker.application.exceptions import GraphPortError

class IssueRepository(Protocol):
    """
    Repository contract for Issue persistence.

    Implementations must:
    - Persist IssueDTO objects.
    - Return IssueDTO on read operations or None if not found.
    - Raise GraphPortError or a subclass for persistence-related failures.
    """

    def save(self, issue: IssueDTO) -> None:
        """Persist or update the issue."""

    def get(self, issue_id: str) -> Optional[IssueDTO]:
        """Return IssueDTO or None if not found."""

    def list(self, status: str | None = None) -> Iterable[IssueSummary]:
        """Return summaries of issues, optionally filtered by status."""

    def delete(self, issue_id: str) -> None:
        """Delete issue by id. No-op if missing."""

class GraphRepository(Protocol):
    """
    Repository contract for graph queries and dependency traversal.

    Implementations must:
    - Provide deterministic traversal results.
    - Return DependencyEdge objects for dependency queries.
    - Raise GraphPortError for graph-related failures.
    """

    def add_dependency(self, edge: DependencyEdge) -> None:
        """Create a dependency edge between issues."""

    def get_dependencies(self, issue_id: str, depth: int = 1) -> Iterable[DependencyEdge]:
        """Return dependency edges reachable from issue_id up to depth."""

    def find_impact_set(self, issue_id: str, max_depth: int = 5) -> Iterable[str]:
        """Return list of issue ids impacted by changes to issue_id (transitive closure)."""
```

---

#### Exact code to add for Neo4j Issue repository

Create `tasker/infrastructure/neo4j_issue_repository.py` with the exact content below.

```python
# tasker/infrastructure/neo4j_issue_repository.py
from __future__ import annotations
from typing import Optional, Iterable
from tasker.application.repositories import IssueRepository
from tasker.application.dtos import IssueDTO, IssueSummary
from tasker.application.ports import GraphPort, QueryResult
from tasker.application.exceptions import GraphPortError

class Neo4jIssueRepository(IssueRepository):
    """
    Neo4j-backed implementation of IssueRepository.

    Implementation notes:
    - Issues are stored as nodes with label Issue and property 'id' (string).
    - Use parameterized Cypher queries only.
    - Map driver results to IssueDTO and IssueSummary.
    """

    def __init__(self, graph: GraphPort) -> None:
        self._graph = graph

    def save(self, issue: IssueDTO) -> None:
        try:
            cypher = (
                "MERGE (i:Issue {id: $id}) "
                "SET i.title = $title, i.description = $description, i.status = $status, i.metadata = $metadata "
            )
            self._graph.run_cypher(cypher, {
                "id": issue.id,
                "title": issue.title,
                "description": issue.description,
                "status": issue.status,
                "metadata": dict(issue.metadata or {}),
            })
        except Exception as exc:
            raise GraphPortError(f"Failed to save issue {issue.id}: {exc}") from exc

    def get(self, issue_id: str) -> Optional[IssueDTO]:
        try:
            cypher = "MATCH (i:Issue {id: $id}) RETURN i.id AS id, i.title AS title, i.description AS description, i.status AS status, i.metadata AS metadata"
            res = self._graph.run_cypher(cypher, {"id": issue_id})
            if not res.records:
                return None
            r = res.records[0]
            return IssueDTO(
                id=str(r.get("id")),
                title=str(r.get("title") or ""),
                description=str(r.get("description") or ""),
                status=str(r.get("status") or ""),
                metadata=r.get("metadata") or {},
            )
        except Exception as exc:
            raise GraphPortError(f"Failed to get issue {issue_id}: {exc}") from exc

    def list(self, status: str | None = None) -> Iterable[IssueSummary]:
        try:
            if status:
                cypher = "MATCH (i:Issue {status: $status}) RETURN i.id AS id, i.title AS title, i.status AS status"
                res = self._graph.run_cypher(cypher, {"status": status})
            else:
                cypher = "MATCH (i:Issue) RETURN i.id AS id, i.title AS title, i.status AS status"
                res = self._graph.run_cypher(cypher, {})
            for r in res.records:
                yield IssueSummary(id=str(r.get("id")), title=str(r.get("title") or ""), status=str(r.get("status") or ""))
        except Exception as exc:
            raise GraphPortError(f"Failed to list issues: {exc}") from exc

    def delete(self, issue_id: str) -> None:
        try:
            cypher = "MATCH (i:Issue {id: $id}) DETACH DELETE i"
            self._graph.run_cypher(cypher, {"id": issue_id})
        except Exception as exc:
            raise GraphPortError(f"Failed to delete issue {issue_id}: {exc}") from exc
```

---

#### Exact code to add for Neo4j Graph repository

Create `tasker/infrastructure/neo4j_graph_repository.py` with the exact content below.

```python
# tasker/infrastructure/neo4j_graph_repository.py
from __future__ import annotations
from typing import Iterable
from tasker.application.repositories import GraphRepository
from tasker.application.dtos import DependencyEdge
from tasker.application.ports import GraphPort
from tasker.application.exceptions import GraphPortError

class Neo4jGraphRepository(GraphRepository):
    """
    Neo4j-backed implementation of GraphRepository.

    Implementation notes:
    - Dependency edges are represented as relationships :DEPENDS_ON between Issue nodes.
    - get_dependencies returns edges with relation 'DEPENDS_ON' and metadata if present.
    - find_impact_set returns list of issue ids reachable via incoming DEPENDS_ON edges (who depends on this issue).
    """

    def __init__(self, graph: GraphPort) -> None:
        self._graph = graph

    def add_dependency(self, edge: DependencyEdge) -> None:
        try:
            cypher = (
                "MATCH (a:Issue {id: $from_id}), (b:Issue {id: $to_id}) "
                "MERGE (a)-[r:DEPENDS_ON]->(b) "
                "SET r.relation = $relation, r.metadata = $metadata"
            )
            self._graph.run_cypher(cypher, {
                "from_id": edge.from_issue_id,
                "to_id": edge.to_issue_id,
                "relation": edge.relation,
                "metadata": dict(edge.metadata or {}),
            })
        except Exception as exc:
            raise GraphPortError(f"Failed to add dependency {edge}: {exc}") from exc

    def get_dependencies(self, issue_id: str, depth: int = 1) -> Iterable[DependencyEdge]:
        try:
            cypher = (
                "MATCH (a:Issue {id: $id})-[r:DEPENDS_ON*1..$depth]->(b:Issue) "
                "UNWIND r AS rel "
                "RETURN a.id AS from_id, b.id AS to_id, rel.relation AS relation, rel.metadata AS metadata"
            )
            res = self._graph.run_cypher(cypher, {"id": issue_id, "depth": depth})
            for r in res.records:
                yield DependencyEdge(
                    from_issue_id=str(r.get("from_id")),
                    to_issue_id=str(r.get("to_id")),
                    relation=str(r.get("relation") or "DEPENDS_ON"),
                    metadata=r.get("metadata") or {},
                )
        except Exception as exc:
            raise GraphPortError(f"Failed to get dependencies for {issue_id}: {exc}") from exc

    def find_impact_set(self, issue_id: str, max_depth: int = 5) -> Iterable[str]:
        try:
            # Find issues that transitively depend on the given issue (reverse traversal)
            cypher = (
                "MATCH (target:Issue {id: $id}) "
                "MATCH (dependent:Issue)-[:DEPENDS_ON*1..$depth]->(target) "
                "RETURN DISTINCT dependent.id AS id"
            )
            res = self._graph.run_cypher(cypher, {"id": issue_id, "depth": max_depth})
            for r in res.records:
                yield str(r.get("id"))
        except Exception as exc:
            raise GraphPortError(f"Failed to compute impact set for {issue_id}: {exc}") from exc
```

---

#### Exact unit tests to add

Create `tests/infrastructure/test_neo4j_issue_repository_unit.py` with the exact content below.

```python
# tests/infrastructure/test_neo4j_issue_repository_unit.py
from unittest.mock import MagicMock
from tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from tasker.application.dtos import IssueDTO

def test_save_and_get_issue_calls_graph_run_cypher():
    graph = MagicMock()
    repo = Neo4jIssueRepository(graph)
    issue = IssueDTO(id="i1", title="T", description="D", status="open", metadata={})
    repo.save(issue)
    assert graph.run_cypher.called
    # Simulate run_cypher returning a record for get
    graph.run_cypher.return_value.records = [{"id": "i1", "title": "T", "description": "D", "status": "open", "metadata": {}}]
    got = repo.get("i1")
    assert got is not None
    assert got.id == "i1"
```

Create `tests/infrastructure/test_neo4j_graph_repository_unit.py` with the exact content below.

```python
# tests/infrastructure/test_neo4j_graph_repository_unit.py
from unittest.mock import MagicMock
from tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from tasker.application.dtos import DependencyEdge

def test_add_dependency_and_find_impact_calls_graph_run_cypher():
    graph = MagicMock()
    repo = Neo4jGraphRepository(graph)
    edge = DependencyEdge(from_issue_id="a", to_issue_id="b", relation="DEPENDS_ON", metadata={})
    repo.add_dependency(edge)
    assert graph.run_cypher.called
    # Simulate find_impact_set
    graph.run_cypher.return_value.records = [{"id": "a"}]
    impacted = list(repo.find_impact_set("b"))
    assert "a" in impacted
```

---

#### Exact integration test to add

Create `tests/integration/test_repositories_integration.py` with the exact content below. This test requires Neo4j running via `docker-compose.neo4j.yml` and uses the `Neo4jGraphAdapter`.

```python
# tests/integration/test_repositories_integration.py
import os
import pytest
from tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from tasker.infrastructure.neo4j_issue_repository import Neo4jIssueRepository
from tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
from tasker.application.dtos import IssueDTO, DependencyEdge

pytestmark = pytest.mark.integration

NEO4J_URI = os.getenv("TASKER_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("TASKER_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("TASKER_NEO4J_PASSWORD", "test")

def test_issue_and_dependency_flow_integration():
    graph = Neo4jGraphAdapter(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    issue_repo = Neo4jIssueRepository(graph)
    graph_repo = Neo4jGraphRepository(graph)

    a = IssueDTO(id="issue-a", title="A", description="A", status="open", metadata={})
    b = IssueDTO(id="issue-b", title="B", description="B", status="open", metadata={})
    issue_repo.save(a)
    issue_repo.save(b)

    edge = DependencyEdge(from_issue_id="issue-a", to_issue_id="issue-b", relation="DEPENDS_ON", metadata={})
    graph_repo.add_dependency(edge)

    impacted = list(graph_repo.find_impact_set("issue-b", max_depth=3))
    assert "issue-a" in impacted

    # cleanup
    issue_repo.delete("issue-a")
    issue_repo.delete("issue-b")
    graph.close()
```

---

#### Documentation exact content

Create `tasker/application/REPOSITORIES.md` with the exact content below.

```
Repository Contracts and Neo4j Implementations

Purpose
- Define IssueRepository and GraphRepository contracts used by application use cases.
- Provide Neo4j-backed implementations that map domain DTOs to graph nodes and relationships.

IssueRepository
- Methods: save(issue), get(issue_id), list(status), delete(issue_id)
- Node label: Issue
- Node property used as primary id: id (string)

GraphRepository
- Methods: add_dependency(edge), get_dependencies(issue_id, depth), find_impact_set(issue_id, max_depth)
- Relationship: DEPENDS_ON
- find_impact_set returns issue ids that transitively depend on the given issue.

Neo4j notes
- All Cypher queries are parameterized.
- Implementations wrap errors as GraphPortError.
- Use docker-compose.neo4j.yml for local integration tests.
```

---

#### Commands the agent must run exactly

```bash
git checkout -b feature/repositories-neo4j
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/infrastructure/test_neo4j_issue_repository_unit.py -q
pytest tests/infrastructure/test_neo4j_graph_repository_unit.py -q
# start neo4j for integration tests if needed
docker compose -f docker-compose.neo4j.yml up -d
# run integration tests
pytest tests/integration/test_repositories_integration.py -q -m integration
# run linters and mypy
ruff check tasker tests
mypy tasker --strict
# commit and push
git add -A
git commit -m "feat(repos): add IssueRepository and GraphRepository protocols and Neo4j implementations with tests"
git push origin feature/repositories-neo4j
```

---

#### PR body exact text to paste

```
Summary:
- Added tasker/application/dtos.py with IssueDTO, IssueSummary, DependencyEdge.
- Added tasker/application/repositories.py with IssueRepository and GraphRepository Protocols.
- Added Neo4j implementations:
  - tasker/infrastructure/neo4j_issue_repository.py
  - tasker/infrastructure/neo4j_graph_repository.py
- Added unit tests for repositories and an integration test that runs against Neo4j.
- Added documentation tasker/application/REPOSITORIES.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests: pytest tests/infrastructure/test_neo4j_issue_repository_unit.py and test_neo4j_graph_repository_unit.py (passed).
3. Started Neo4j via docker compose: docker compose -f docker-compose.neo4j.yml up -d
4. Ran integration tests: pytest tests/integration/test_repositories_integration.py -m integration (passed).
5. Ran linters and type checks: ruff, mypy --strict.

Files changed:
- tasker/application/dtos.py
- tasker/application/repositories.py
- tasker/application/REPOSITORIES.md
- tasker/infrastructure/neo4j_issue_repository.py
- tasker/infrastructure/neo4j_graph_repository.py
- tests/infrastructure/test_neo4j_issue_repository_unit.py
- tests/infrastructure/test_neo4j_graph_repository_unit.py
- tests/integration/test_repositories_integration.py

Notes:
- Repositories depend only on GraphPort Protocol; Neo4j-specific logic is contained in infrastructure adapters.
- All queries are parameterized to avoid injection and to be testable.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `tasker/application/dtos.py` exists and matches the provided code.
- `tasker/application/repositories.py` exists and matches the provided code.
- `tasker/infrastructure/neo4j_issue_repository.py` and `tasker/infrastructure/neo4j_graph_repository.py` exist and implement the methods specified by the Protocols.
- Unit tests `tests/infrastructure/test_neo4j_issue_repository_unit.py` and `tests/infrastructure/test_neo4j_graph_repository_unit.py` pass.
- Integration test `tests/integration/test_repositories_integration.py` passes when Neo4j is available via `docker-compose.neo4j.yml`.
- Documentation `tasker/application/REPOSITORIES.md` exists and documents contracts and Neo4j notes.
- Branch `feature/repositories-neo4j` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `architecture`
- `infra`
- `neo4j`
- `tests`
- `medium-priority`

---

#### Estimated effort
**Medium (M)** — expected to take an autonomous agent or engineer **2–6 hours** depending on test environment and CI.

---