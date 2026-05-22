### Issue 289 — **Modularize repository into `domain`, `application`, `infrastructure`, and `cli` packages**

**Short description**  
Reorganize the Python package layout so the project is explicitly split into four orthogonal layers: **`domain`** (entities, value objects, domain rules), **`application`** (use cases / services / ports), **`infrastructure`** (adapters for Neo4j, Tree‑Sitter, Git, embeddings, persistence), and **`cli`** (argument parsing, wiring, entrypoints). The goal is to make the codebase unambiguous for an autonomous agent: every file has a single responsibility and imports follow the rule *application → domain; cli → application; infrastructure implements ports defined by application; domain does not import infrastructure or cli*.

---

#### Objective (what the agent must deliver)
1. Create the new package layout under the repository root:
   ```
   tasker/
     domain/
     application/
     infrastructure/
     cli/
     tests/
     examples/
     pyproject.toml
     setup.cfg (if present)
     README.md
   ```
2. Move existing modules into the appropriate package with minimal behavioral changes.
3. Update all imports so tests and CLI run without import errors.
4. Add `__init__.py` files that export only the public API for each package.
5. Add a **migration checklist** file `REFACTORING/MOVE_LOG.md` documenting every file moved and the original path → new path mapping.
6. Add a GitHub Pull Request description template (in the PR body) that lists the files moved and the verification steps executed by the agent.
7. Ensure CI (if present) passes after the reorganization.

---

#### Why this must be done exactly this way
- Prevents domain logic from depending on infrastructure details.
- Makes it trivial for other agents to find and call use cases and to implement new adapters.
- Removes ambiguity about where to add new code (agents will not guess).

---

#### Detailed step‑by‑step instructions (strict, actionable)

1. **Create package directories**
   - If `tasker/` does not exist, create it and move top-level Python package files into it.
   - Create directories: `tasker/domain`, `tasker/application`, `tasker/infrastructure`, `tasker/cli`.
   - Add `__init__.py` to each directory. Each `__init__.py` must be minimal and only export the package public API (see step 4).

2. **Inventory current Python modules**
   - Run:
     ```bash
     git ls-files '*.py' | sed -e 's|^|./|' > /tmp/python_files.txt
     ```
   - Filter out tests and scripts in `tests/`, `examples/`, `docs/`.
   - Produce a mapping table `REFACTORING/MOVE_LOG.md` with columns: `original_path | new_path | reason`.

3. **Classify each module into one of the four packages**
   - **Domain**: modules that define entities, value objects, domain exceptions, domain-level invariants, domain events. Example names: `issue.py`, `task.py`, `reasoning_node.py`, `entities.py`.
   - **Application**: modules that implement use cases, orchestrators, service interfaces (ports), DTOs for use cases. Example names: `use_cases.py`, `ports.py`, `services.py`, `commands.py`.
   - **Infrastructure**: modules that interact with external systems (Neo4j drivers, Tree‑Sitter parsing, Git operations, embedding storage, vector DB). Example names: `neo4j_adapter.py`, `treesitter_adapter.py`, `git_adapter.py`, `faiss_adapter.py`.
   - **CLI**: modules that parse CLI args, configure logging, wire dependencies and call application use cases. Example names: `cli.py`, `main.py`, `entrypoint.py`.
   - **If a module mixes responsibilities**, split it into two files before moving: one for domain/application and one for infra/cli. The agent must not leave mixed‑responsibility files.

4. **Move files and update imports**
   - For each file in the mapping:
     - Create the destination directory if missing.
     - Move the file with `git mv`.
     - Update all import statements across the repository to the new dotted path.
       - Use a deterministic search-and-replace approach:
         ```bash
         # Example: replace "from tasker_old import issue" with "from tasker.domain import issue"
         python - <<'PY'
         import re,sys,subprocess,os
         # load mapping from REFACTORING/MOVE_LOG.md and apply replacements
         PY
         ```
       - The agent must update both `import X` and `from X import Y` forms.
       - Do not change relative imports inside a package except to convert them to absolute imports consistent with the new package layout.
   - **Important:** After moving each file, run `python -m pip install -e .` (or the project’s install command) and run the test suite to detect import errors early.

5. **Design `__init__.py` exports**
   - Each package `__init__.py` must:
     - Import and re-export only the public classes/functions used by other packages.
     - Example for `tasker/domain/__init__.py`:
       ```python
       from .issue import Issue
       from .task import Task
       __all__ = ["Issue", "Task"]
       ```
   - Do not import infrastructure modules in domain `__init__.py`.

6. **Add a compatibility shim (temporary)**
   - If external scripts or CI reference old import paths, add a compatibility shim module at the old path that raises a clear error instructing to update imports, or better, re-export from the new path for a short period.
   - Example `tasker_old.py`:
     ```python
     from tasker.domain.issue import Issue
     raise DeprecationWarning("Import path changed: use tasker.domain.Issue")
     ```
   - Document in `REFACTORING/MOVE_LOG.md` when the shim can be removed.

7. **Update packaging metadata**
   - If `pyproject.toml`, `setup.cfg`, or `setup.py` reference package names or package_dir, update them to include the new `tasker` package and subpackages.
   - Ensure `pyproject.toml` `packages` or `tool.poetry.packages` includes `tasker` and subpackages.

8. **Run static checks and tests**
   - Run linters and type checks:
     ```bash
     pre-commit run --all-files || true
     ruff check .
     mypy tasker --ignore-missing-imports
     ```
   - Run unit tests:
     ```bash
     pytest -q
     ```
   - Fix any import or test failures iteratively.

9. **Commit and push**
   - Create a single feature branch `refactor/modularize-packages`.
   - Commit with a clear message:
     ```
     git checkout -b refactor/modularize-packages
     git add -A
     git commit -m "refactor: reorganize code into domain, application, infrastructure, cli packages"
     git push origin refactor/modularize-packages
     ```
   - Open a PR with the following PR body (exact text to paste):
     ```
     Summary:
     - Reorganized repository into four packages: tasker.domain, tasker.application, tasker.infrastructure, tasker.cli
     - Moved files as documented in REFACTORING/MOVE_LOG.md
     - Added compatibility shims where necessary
     - Updated packaging metadata and CI to reference new package layout

     Verification steps executed by this agent:
     1. Installed package in editable mode: python -m pip install -e .
     2. Ran linters: ruff, mypy (domain/application strict)
     3. Ran tests: pytest (all tests passed)
     4. Verified CLI commands: python -m tasker.cli.main --help

     Files moved:
     (paste REFACTORING/MOVE_LOG.md content here)

     Notes:
     - Compatibility shims are temporary and should be removed after downstream updates.
     ```

10. **Post‑merge cleanup**
    - After PR is merged, create a follow-up issue to remove compatibility shims and to update any external documentation referencing old import paths.

---

#### Acceptance criteria (must be satisfied exactly)
- **All Python modules are inside `tasker/domain`, `tasker/application`, `tasker/infrastructure`, or `tasker/cli`.**
- **No file in `tasker/domain` imports anything from `tasker/infrastructure` or `tasker.cli`.**
- **`REFACTORING/MOVE_LOG.md` exists and lists every moved file with original and new paths.**
- **`__init__.py` files export only the public API for each package.**
- **Project installs in editable mode and `pytest` completes with no import errors.**
- **CI workflow (if present) still runs and passes lint + tests.**
- **PR created on branch `refactor/modularize-packages` with the exact PR body described above.**

---

#### Labels to apply on GitHub
- `refactor`
- `architecture`
- `high-priority`
- `good-first-issue` (optional, if you want contributors to help)

---

#### Estimated effort
**Medium (M)** — expected to take an experienced engineer or an autonomous agent with file-move and import-refactor capabilities **4–12 hours** depending on repository size and test coverage.

---

#### Files and commands the agent must modify or run (explicit)
- **Files to create**
  - `tasker/domain/__init__.py`
  - `tasker/application/__init__.py`
  - `tasker/infrastructure/__init__.py`
  - `tasker/cli/__init__.py`
  - `REFACTORING/MOVE_LOG.md`
- **Commands to run**
  ```bash
  git checkout -b refactor/modularize-packages
  mkdir -p tasker/{domain,application,infrastructure,cli}
  # move files using git mv
  git ls-files '*.py' > /tmp/python_files.txt
  # run tests and linters
  python -m pip install -e .
  pre-commit run --all-files || true
  ruff check .
  mypy tasker --ignore-missing-imports
  pytest -q
  git add -A
  git commit -m "refactor: reorganize code into domain, application, infrastructure, cli"
  git push origin refactor/modularize-packages
  ```
- **CI file to check**
  - `.github/workflows/ci.yml` (update package paths if necessary)

---

#### Example of a minimal `tasker/application/ports.py` to add (exact code)
```python
from typing import Protocol, Iterable, Any
from tasker.domain.issue import Issue

class GraphPort(Protocol):
    def create_node(self, label: str, properties: dict) -> str: ...
    def run_cypher(self, query: str, params: dict | None = None) -> Iterable[dict]: ...

class ParserPort(Protocol):
    def parse_file(self, path: str) -> dict: ...
    def extract_symbols(self, ast: dict) -> Iterable[dict]: ...

class GitPort(Protocol):
    def list_changed_files(self, commit_ref: str) -> Iterable[str]: ...

class EmbeddingPort(Protocol):
    def embed_text(self, text: str) -> list[float]: ...
```
- The agent must place this file in `tasker/application/ports.py` and ensure infrastructure adapters implement these protocols.

---

#### PR checklist (must be included in PR description)
- [ ] `REFACTORING/MOVE_LOG.md` added and complete.
- [ ] All imports updated and tests pass locally.
- [ ] `__init__.py` exports reviewed.
- [ ] Packaging metadata updated.
- [ ] CI passes on the branch.
- [ ] Compatibility shims documented.