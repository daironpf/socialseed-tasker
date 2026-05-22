### Issue 290 — Define application ports and protocols for external adapters

**Short description**  
Create a single, explicit module that defines all **ports** (Protocol interfaces) used by the application layer to interact with external systems. The module must be the canonical contract that every infrastructure adapter implements. The goal is to remove ambiguity for autonomous agents: adapters must implement these exact methods and signatures so the agent can wire dependencies without guessing.

---

#### Objective (what the agent must deliver)
1. Add a new file `tasker/application/ports.py` that contains typed `Protocol` definitions for all external dependencies the application uses: **GraphPort**, **ParserPort**, **GitPort**, **EmbeddingPort**, **StoragePort**, and **LoggerPort**.
2. Each `Protocol` must include method names, parameter types, return types, and docstrings describing behavior, error semantics, and side effects.
3. Add unit tests that verify a minimal concrete adapter stub conforms to each `Protocol` using `typing.runtime_checkable` and `isinstance` checks where applicable.
4. Update any existing infrastructure adapters to explicitly declare they implement the corresponding `Protocol` (via type hints or `# type: ignore` only if necessary).
5. Add a short README `tasker/application/PORTS.md` that documents the contract, expected exceptions, and examples of usage for each port.
6. Create a PR branch `feature/define-application-ports` with the changes and a PR body that lists the ports and verification steps.

---

#### Why this must be done exactly this way
- Ensures **strict, machine-readable contracts** between application and infrastructure.
- Prevents agents from implementing adapters with incompatible method names or signatures.
- Makes mocking and testing deterministic for autonomous agents.

---

#### Detailed step‑by‑step instructions (strict, actionable)

1. **Create the file**
   - Path: `tasker/application/ports.py`
   - Add the exact code block below (copy-paste). Do not alter method names or signatures.

```python
# tasker/application/ports.py
from __future__ import annotations
from typing import Protocol, Iterable, Mapping, Any, Optional, runtime_checkable
from dataclasses import dataclass

@dataclass
class NodeRecord:
    id: str
    labels: list[str]
    properties: dict[str, Any]

@dataclass
class QueryResult:
    records: list[Mapping[str, Any]]

@runtime_checkable
class GraphPort(Protocol):
    """
    Minimal graph database contract used by application use cases.

    Implementations must:
    - Use stable string node ids for create_node return values.
    - Raise GraphPortError on transient failures.
    - Not mutate input dicts.
    """

    def create_node(self, label: str, properties: dict[str, Any]) -> str:
        """Create a node with label and properties. Return node id as string."""

    def get_node(self, node_id: str) -> Optional[NodeRecord]:
        """Return NodeRecord or None if not found."""

    def run_cypher(self, query: str, params: Optional[dict[str, Any]] = None) -> QueryResult:
        """Execute a read or write Cypher query and return structured results."""

    def delete_node(self, node_id: str) -> None:
        """Delete node by id. No-op if node does not exist."""

@runtime_checkable
class ParserPort(Protocol):
    """
    Code parser contract.

    Implementations must:
    - Return deterministic AST-like structures for the same input.
    - Not raise on parseable files; raise ParserError on unreadable files.
    """

    def parse_file(self, path: str) -> dict[str, Any]:
        """Parse a source file and return an AST-like dict."""

    def extract_symbols(self, ast: dict[str, Any]) -> list[dict[str, Any]]:
        """Return a list of symbol descriptors extracted from AST."""

    def extract_imports(self, ast: dict[str, Any]) -> list[str]:
        """Return a list of import targets (module paths or file paths)."""

@runtime_checkable
class GitPort(Protocol):
    """
    Git operations contract.

    Implementations must be read-only unless explicitly named 'apply_patch'.
    """

    def list_changed_files(self, ref: str) -> list[str]:
        """Return list of file paths changed in the given commit/ref."""

    def read_file_at_ref(self, path: str, ref: str) -> str:
        """Return file contents at the given ref."""

    def current_branch(self) -> str:
        """Return current branch name."""

@runtime_checkable
class EmbeddingPort(Protocol):
    """
    Text embedding contract.

    Implementations must return a fixed-length list of floats for the same input text.
    """

    def embed_text(self, text: str) -> list[float]:
        """Return embedding vector for the provided text."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a batch of texts in the same order."""

@runtime_checkable
class StoragePort(Protocol):
    """
    Generic key-value storage contract for caching and RAG artifacts.
    """

    def put(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        """Store value under key. Overwrite if exists."""

    def get(self, key: str) -> Optional[bytes]:
        """Return value or None if missing."""

    def delete(self, key: str) -> None:
        """Delete key if exists."""

@runtime_checkable
class LoggerPort(Protocol):
    """
    Minimal structured logging contract used by application code.
    """

    def info(self, message: str, **fields: Any) -> None: ...
    def debug(self, message: str, **fields: Any) -> None: ...
    def warning(self, message: str, **fields: Any) -> None: ...
    def error(self, message: str, **fields: Any) -> None: ...
```

2. **Add typed exceptions file**
   - Create `tasker/application/exceptions.py` with the exact content below.

```python
# tasker/application/exceptions.py
class GraphPortError(Exception):
    """Transient or permanent graph database error."""

class ParserError(Exception):
    """Parsing failed due to unreadable or invalid input."""

class GitError(Exception):
    """Git operation failed."""

class EmbeddingError(Exception):
    """Embedding generation failed."""

class StorageError(Exception):
    """Storage operation failed."""
```

3. **Create PORTS documentation**
   - File: `tasker/application/PORTS.md`
   - Content must include:
     - One-paragraph description of each port.
     - Example call for each method (input and expected output shape).
     - Expected exceptions for each port method (map to exceptions in `exceptions.py`).
   - The agent must produce the file with concrete examples (short code snippets) for each method.

4. **Add conformance unit tests**
   - File: `tests/application/test_ports_conformance.py`
   - The test must:
     - Import the `Protocol` classes and create minimal concrete stubs that implement the methods.
     - Use `isinstance(stub, GraphPort)` style checks where `runtime_checkable` applies.
     - Use `mypy`-friendly static checks by assigning stubs to typed variables.
   - Exact test code to add:

```python
# tests/application/test_ports_conformance.py
from tasker.application import ports
from tasker.application import exceptions

class DummyGraph:
    def create_node(self, label: str, properties: dict) -> str:
        return "node-1"
    def get_node(self, node_id: str):
        return None
    def run_cypher(self, query: str, params=None):
        return ports.QueryResult(records=[])
    def delete_node(self, node_id: str) -> None:
        return None

def test_graph_port_runtime_checkable():
    g = DummyGraph()
    assert isinstance(g, ports.GraphPort)

def test_embedding_port_signature():
    class DummyEmbed:
        def embed_text(self, text: str):
            return [0.0] * 8
        def embed_batch(self, texts: list[str]):
            return [[0.0] * 8 for _ in texts]
    e: ports.EmbeddingPort = DummyEmbed()
    assert isinstance(e, ports.EmbeddingPort)
```

5. **Update existing adapters**
   - For each adapter in `tasker/infrastructure` that implements one of these ports, add explicit type annotations on the class definition or constructor to indicate the implemented `Protocol`. Example:

```python
from tasker.application.ports import GraphPort

class Neo4jGraphAdapter(GraphPort):
    ...
```

   - If the adapter cannot be modified to inherit the Protocol (e.g., third-party wrapper), add a small adapter shim in `tasker/infrastructure/shims/` that implements the Protocol and delegates to the wrapper.

6. **Run static type checks and tests**
   - Commands to run:

```bash
git checkout -b feature/define-application-ports
python -m pip install -e .
ruff check tasker tests
mypy tasker --strict
pytest tests/application/test_ports_conformance.py -q
```

   - Fix any type errors or test failures. The agent must not bypass `mypy` errors with `# type: ignore` except in a documented shim with a comment explaining why.

7. **Commit, push, and open PR**
   - Commit message:
     ```
     feat(application): add typed Protocol ports and conformance tests
     ```
   - Push branch `feature/define-application-ports`.
   - PR body (exact text to paste):

```
Summary:
- Added tasker/application/ports.py with Protocol definitions for GraphPort, ParserPort, GitPort, EmbeddingPort, StoragePort, LoggerPort.
- Added tasker/application/exceptions.py with typed exceptions.
- Added PORTS.md documenting contracts and examples.
- Added tests/application/test_ports_conformance.py to verify runtime conformance.
- Updated infrastructure adapters to explicitly implement ports or added shims.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran linters: ruff check tasker tests.
3. Ran mypy: mypy tasker --strict.
4. Ran unit tests: pytest tests/application/test_ports_conformance.py (passed).

Files changed:
- tasker/application/ports.py
- tasker/application/exceptions.py
- tasker/application/PORTS.md
- tests/application/test_ports_conformance.py
- (plus adapter updates or shims in tasker/infrastructure/)

Notes:
- Adapters must implement these Protocols exactly. If an adapter cannot be changed, add a shim in tasker/infrastructure/shims/.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `tasker/application/ports.py` exists and matches the provided code block exactly.
- `tasker/application/exceptions.py` exists and matches the provided code block exactly.
- `tasker/application/PORTS.md` documents each port with examples and expected exceptions.
- `tests/application/test_ports_conformance.py` exists and passes.
- All infrastructure adapters either:
  - Explicitly inherit the corresponding `Protocol`, or
  - Have a shim in `tasker/infrastructure/shims/` that implements the `Protocol` and delegates.
- `mypy tasker --strict` completes with no errors in the `tasker/application` package.
- PR `feature/define-application-ports` created with the exact PR body above.

---

#### Labels to apply on GitHub
- `design`
- `typing`
- `good-first-issue`
- `medium-priority`

---

#### Estimated effort
**Small (S)** — expected to take an autonomous agent or engineer **1–3 hours**.

---

#### Files and commands the agent must modify or run (explicit)
- **Files to create**
  - `tasker/application/ports.py`
  - `tasker/application/exceptions.py`
  - `tasker/application/PORTS.md`
  - `tests/application/test_ports_conformance.py`
- **Commands to run**
```bash
git checkout -b feature/define-application-ports
python -m pip install -e .
ruff check tasker tests
mypy tasker --strict
pytest tests/application/test_ports_conformance.py -q
git add -A
git commit -m "feat(application): add typed Protocol ports and conformance tests"
git push origin feature/define-application-ports
```


