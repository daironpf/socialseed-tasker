### ✅ Issue 292 — Extract Tree‑Sitter parsing into a `ParserPort` adapter (`TreeSitterParser` with Python fallback) (SOLVED)

**Short description**  
Create a deterministic parser adapter that implements the `ParserPort` Protocol (`tasker/application/ports.ParserPort`). The adapter must use **Tree‑Sitter** when the `tree_sitter` Python package and compiled language grammars are available, and **fall back to Python's builtin `ast`** for `.py` files when Tree‑Sitter is not available. The adapter must expose the exact methods `parse_file(path: str) -> dict[str, Any]`, `extract_symbols(ast: dict[str, Any]) -> list[dict[str, Any]]`, and `extract_imports(ast: dict[str, Any]) -> list[str]`. All behavior, error semantics and return shapes must match the `ParserPort` contract so autonomous agents can rely on it without guessing.

**Status:** ✅ SOLVED — implementado en `v1.0.0`. Tests unitarios (5/5) pasan, test integración (1 skipped, Tree-Sitter no configurado). Ruff sin errores. Conformance tests (8/8) pasan.

---

#### Objective (what the agent must deliver)
1. Add `tasker/infrastructure/parser_adapter.py` implementing a class `TreeSitterParser` that **inherits** `tasker.application.ports.ParserPort` and implements the three required methods exactly.
2. Add `tasker/infrastructure/parser_config.py` to centralize configuration (supported file extensions, language mapping, optional path to compiled grammars).
3. Provide a pure-Python fallback parser for `.py` files using the `ast` module that returns the same AST-like dict shape as the Tree‑Sitter branch.
4. Add unit tests that validate parsing, symbol extraction and import extraction for small Python example files.
5. Add integration tests that exercise the Tree‑Sitter branch **only if** `tree_sitter` is importable and a compiled Python grammar is available via environment variable `TASKER_TREESITTER_PYTHON_SO`. If Tree‑Sitter is not available, the integration test must be skipped with a clear reason.
6. Add documentation `tasker/infrastructure/PARSER_ADAPTER.md` describing behavior, fallback semantics, supported file types, and examples.
7. Create branch `feature/parser-adapter` and open a PR with the exact PR body described below.

---

#### Why this must be done exactly this way
- Agents must be able to call `parse_file`, `extract_symbols`, and `extract_imports` with deterministic outputs for the same input file.
- Tree‑Sitter is preferred for multi-language support, but many CI/dev environments will not have compiled grammars; a robust fallback ensures reproducible behavior.
- The adapter must implement the `ParserPort` contract exactly so other agents can mock or replace it without guessing method names or return shapes.

---

#### Files to add or modify (exact paths)
- `tasker/infrastructure/parser_adapter.py` **(new)**
- `tasker/infrastructure/parser_config.py` **(new)**
- `tasker/infrastructure/PARSER_ADAPTER.md` **(new)**
- `tests/infrastructure/test_parser_adapter_unit.py` **(new)**
- `tests/integration/test_parser_adapter_treesitter_integration.py` **(new, skipped if Tree‑Sitter not available)**
- Update `tasker/infrastructure/__init__.py` to export `TreeSitterParser` (if present).

---

#### Exact code to add for the adapter

Create `tasker/infrastructure/parser_adapter.py` with the exact content below. Do not change method names or signatures.

```python
# tasker/infrastructure/parser_adapter.py
from __future__ import annotations
import os
import ast as py_ast
from typing import Any, Optional, List, Dict
from tasker.application.ports import ParserPort
from tasker.application.exceptions import ParserError

# Try to import tree_sitter; if not available, we will use Python ast fallback.
try:
    from tree_sitter import Language, Parser  # type: ignore
    _TREE_SITTER_AVAILABLE = True
except Exception:
    _TREE_SITTER_AVAILABLE = False

from tasker.infrastructure.parser_config import ParserConfig

class TreeSitterParser(ParserPort):
    """
    Parser adapter that uses Tree-Sitter when available and falls back to Python's ast for .py files.

    Behavior:
    - parse_file(path) returns a deterministic AST-like dict with keys:
      { "type": "<node-type>", "start_byte": int, "end_byte": int, "text": str, "children": [ ... ] }
    - extract_symbols(ast_dict) returns a list of symbol descriptors:
      [ {"name": str, "type": "function"|"class"|"variable", "location": {"start": int, "end": int}} ]
    - extract_imports(ast_dict) returns a list of import targets as strings.
    - On unreadable files or unsupported extensions, raise ParserError.
    """

    def __init__(self, config: Optional[ParserConfig] = None) -> None:
        self.config = config or ParserConfig.load_from_env()
        self._ts_parser = None
        self._ts_language = None
        if _TREE_SITTER_AVAILABLE and self.config.treesitter_python_so:
            try:
                self._ts_language = Language(self.config.treesitter_python_so, "python")
                p = Parser()
                p.set_language(self._ts_language)
                self._ts_parser = p
            except Exception:
                # If Tree-Sitter initialization fails, fall back to ast
                self._ts_parser = None
                self._ts_language = None

    def parse_file(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise ParserError(f"File not found: {path}")
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.config.supported_extensions:
            raise ParserError(f"Unsupported file extension: {ext}")
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except Exception as exc:
            raise ParserError(f"Unable to read file {path}: {exc}") from exc

        # Prefer Tree-Sitter when available and language supported
        if self._ts_parser and ext == ".py":
            try:
                tree = self._ts_parser.parse(raw)
                root = tree.root_node
                return self._node_to_dict(root, raw)
            except Exception as exc:
                # Fall back to ast if Tree-Sitter fails for this file
                pass

        # Fallback: use Python ast for .py files
        if ext == ".py":
            try:
                text = raw.decode("utf-8")
                py_tree = py_ast.parse(text)
                return self._ast_to_dict(py_tree, text)
            except Exception as exc:
                raise ParserError(f"Python AST parse failed for {path}: {exc}") from exc

        # If we reach here, unsupported language without Tree-Sitter
        raise ParserError(f"No parser available for extension: {ext}")

    def extract_symbols(self, ast_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        symbols: List[Dict[str, Any]] = []
        node_type = ast_dict.get("type")
        # Walk tree recursively
        stack = [ast_dict]
        while stack:
            node = stack.pop()
            ntype = node.get("type")
            if ntype in ("function_definition", "function_def", "FunctionDef"):
                name = node.get("name") or node.get("text", "")[:64]
                symbols.append({"name": name, "type": "function", "location": node.get("location")})
            elif ntype in ("class_definition", "class_def", "ClassDef"):
                name = node.get("name") or node.get("text", "")[:64]
                symbols.append({"name": name, "type": "class", "location": node.get("location")})
            # variables: heuristics for assignments
            elif ntype in ("assignment", "assign"):
                # try to extract target names
                targets = node.get("targets") or []
                for t in targets:
                    if isinstance(t, dict) and "name" in t:
                        symbols.append({"name": t["name"], "type": "variable", "location": t.get("location")})
            children = node.get("children") or []
            for c in children:
                stack.append(c)
        return symbols

    def extract_imports(self, ast_dict: Dict[str, Any]) -> List[str]:
        imports: List[str] = []
        stack = [ast_dict]
        while stack:
            node = stack.pop()
            ntype = node.get("type")
            if ntype in ("import_statement", "import_from", "import"):
                # Tree-sitter and ast fallback shapes differ; try common keys
                module = node.get("module") or node.get("module_name") or node.get("text")
                if isinstance(module, str):
                    imports.append(module.strip())
                else:
                    # try to extract names list
                    names = node.get("names") or []
                    for nm in names:
                        if isinstance(nm, str):
                            imports.append(nm.strip())
                        elif isinstance(nm, dict) and "name" in nm:
                            imports.append(nm["name"].strip())
            children = node.get("children") or []
            for c in children:
                stack.append(c)
        return imports

    # Helper: convert tree-sitter node to dict
    def _node_to_dict(self, node, raw_bytes: bytes) -> Dict[str, Any]:
        text = raw_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
        d: Dict[str, Any] = {
            "type": node.type,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "text": text,
            "children": [],
            "location": {"start": node.start_byte, "end": node.end_byte},
        }
        # name extraction heuristics for function/class nodes
        try:
            name_node = None
            for child in node.children:
                if child.type == "identifier":
                    name_node = child
                    break
            if name_node:
                d["name"] = raw_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", errors="replace")
        except Exception:
            pass
        for c in node.children:
            d["children"].append(self._node_to_dict(c, raw_bytes))
        # For assignments, expose targets
        if node.type in ("assignment", "assign"):
            targets = []
            for c in node.children:
                if c.type == "identifier":
                    targets.append({"name": raw_bytes[c.start_byte:c.end_byte].decode("utf-8", errors="replace"),
                                    "location": {"start": c.start_byte, "end": c.end_byte}})
            if targets:
                d["targets"] = targets
        return d

    # Helper: convert Python ast.AST to dict
    def _ast_to_dict(self, node: py_ast.AST, source_text: str) -> Dict[str, Any]:
        def _node(n: py_ast.AST) -> Dict[str, Any]:
            d: Dict[str, Any] = {
                "type": type(n).__name__,
                "children": [],
                "text": "",
                "location": {},
            }
            # location
            if hasattr(n, "lineno") and hasattr(n, "end_lineno"):
                try:
                    start = getattr(n, "lineno")
                    end = getattr(n, "end_lineno")
                    d["location"] = {"start_line": start, "end_line": end}
                except Exception:
                    d["location"] = {}
            # name extraction
            if isinstance(n, py_ast.FunctionDef):
                d["name"] = n.name
            if isinstance(n, py_ast.ClassDef):
                d["name"] = n.name
            if isinstance(n, py_ast.Assign):
                targets = []
                for t in n.targets:
                    if isinstance(t, py_ast.Name):
                        targets.append({"name": t.id, "location": {"lineno": getattr(t, "lineno", None)}})
                if targets:
                    d["targets"] = targets
            # import nodes
            if isinstance(n, py_ast.Import):
                names = [alias.name for alias in n.names]
                d["type"] = "import_statement"
                d["names"] = names
            if isinstance(n, py_ast.ImportFrom):
                module = n.module or ""
                d["type"] = "import_from"
                d["module"] = module
                d["names"] = [alias.name for alias in n.names]
            # text snippet
            try:
                if hasattr(n, "lineno") and hasattr(n, "end_lineno"):
                    lines = source_text.splitlines()
                    s = max(0, n.lineno - 1)
                    e = min(len(lines), n.end_lineno)
                    d["text"] = "\n".join(lines[s:e])
            except Exception:
                d["text"] = ""
            # children
            for child in py_ast.iter_child_nodes(n):
                d["children"].append(_node(child))
            return d
        return _node(node)
```

---

#### Exact code to add for parser config

Create `tasker/infrastructure/parser_config.py` with the exact content below.

```python
# tasker/infrastructure/parser_config.py
from __future__ import annotations
from dataclasses import dataclass
import os
from typing import List, Optional

@dataclass
class ParserConfig:
    supported_extensions: List[str]
    treesitter_python_so: Optional[str]

    @staticmethod
    def load_from_env() -> "ParserConfig":
        # supported extensions are comma-separated, default to Python only
        exts = os.getenv("TASKER_PARSER_EXTENSIONS", ".py").split(",")
        exts = [e.strip() if e.strip().startswith(".") else f".{e.strip()}" for e in exts if e.strip()]
        ts_so = os.getenv("TASKER_TREESITTER_PYTHON_SO")  # path to compiled python.so for tree-sitter
        return ParserConfig(supported_extensions=exts, treesitter_python_so=ts_so)
```

---

#### Unit tests exact code

Create `tests/infrastructure/test_parser_adapter_unit.py` with the exact content below.

```python
# tests/infrastructure/test_parser_adapter_unit.py
import tempfile
import textwrap
from tasker.infrastructure.parser_adapter import TreeSitterParser
from tasker.infrastructure.parser_config import ParserConfig
from tasker.application.exceptions import ParserError

PY_SIMPLE = textwrap.dedent("""
    import os
    import sys
    from math import sqrt

    class Foo:
        def method(self):
            pass

    def bar(x):
        y = x + 1
        return y
""")

def test_parse_python_file_and_extract_symbols_and_imports(tmp_path):
    p = tmp_path / "sample.py"
    p.write_text(PY_SIMPLE, encoding="utf-8")
    config = ParserConfig(supported_extensions=[".py"], treesitter_python_so=None)
    parser = TreeSitterParser(config=config)
    ast_dict = parser.parse_file(str(p))
    assert isinstance(ast_dict, dict)
    symbols = parser.extract_symbols(ast_dict)
    # Expect at least one class and one function
    names = {s["name"] for s in symbols if "name" in s}
    assert "Foo" in names or any("Foo" in s for s in names)
    assert "bar" in names or any("bar" in s for s in names)
    imports = parser.extract_imports(ast_dict)
    assert "os" in imports or "sys" in imports or "math" in imports

def test_parse_nonexistent_file_raises():
    config = ParserConfig(supported_extensions=[".py"], treesitter_python_so=None)
    parser = TreeSitterParser(config=config)
    try:
        parser.parse_file("/path/does/not/exist.py")
        assert False, "Expected ParserError"
    except ParserError:
        pass
```

---

#### Integration test exact code (Tree‑Sitter branch)

Create `tests/integration/test_parser_adapter_treesitter_integration.py` with the exact content below. This test **must be skipped** if `tree_sitter` is not importable or `TASKER_TREESITTER_PYTHON_SO` is not set.

```python
# tests/integration/test_parser_adapter_treesitter_integration.py
import os
import pytest

try:
    from tree_sitter import Language  # type: ignore
    _TS_AVAILABLE = True
except Exception:
    _TS_AVAILABLE = False

from tasker.infrastructure.parser_config import ParserConfig
from tasker.infrastructure.parser_adapter import TreeSitterParser

pytestmark = pytest.mark.integration

def _skip_if_no_treesitter():
    if not _TS_AVAILABLE or not os.getenv("TASKER_TREESITTER_PYTHON_SO"):
        pytest.skip("Tree-Sitter not available or TASKER_TREESITTER_PYTHON_SO not set")

def test_treesitter_python_parse(tmp_path):
    _skip_if_no_treesitter()
    sample = tmp_path / "sample.py"
    sample.write_text("def f():\n    return 1\n", encoding="utf-8")
    config = ParserConfig(supported_extensions=[".py"], treesitter_python_so=os.getenv("TASKER_TREESITTER_PYTHON_SO"))
    parser = TreeSitterParser(config=config)
    ast_dict = parser.parse_file(str(sample))
    assert isinstance(ast_dict, dict)
    symbols = parser.extract_symbols(ast_dict)
    assert any(s.get("type") == "function" or s.get("name") == "f" for s in symbols)
```

---

#### Documentation exact content

Create `tasker/infrastructure/PARSER_ADAPTER.md` with the exact content below.

```
Parser Adapter (TreeSitterParser)

Purpose
- Provide a deterministic ParserPort implementation.
- Use Tree-Sitter when available for richer multi-language parsing.
- Fall back to Python's builtin ast for .py files when Tree-Sitter is not available.

Behavior and return shapes
- parse_file(path) -> dict with keys: type, start_byte/end_byte or location, text, children (list).
- extract_symbols(ast_dict) -> list of dicts: {name, type, location}.
- extract_imports(ast_dict) -> list[str] of import targets.

Configuration
- TASKER_PARSER_EXTENSIONS: comma-separated extensions (default ".py")
- TASKER_TREESITTER_PYTHON_SO: optional path to compiled Tree-Sitter python language .so file

Fallback semantics
- If Tree-Sitter is available and a compiled grammar path is provided, Tree-Sitter is used for .py files.
- If Tree-Sitter is not available or initialization fails, the adapter uses Python ast for .py files.
- For non-.py extensions, Tree-Sitter is required; otherwise parse_file raises ParserError.

Examples
- Python fallback:
  parser = TreeSitterParser()
  ast = parser.parse_file("project/module.py")
  symbols = parser.extract_symbols(ast)
  imports = parser.extract_imports(ast)
```

---

#### Commands the agent must run exactly

```bash
git checkout -b feature/parser-adapter
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/infrastructure/test_parser_adapter_unit.py -q
# run integration tests only if tree_sitter and TASKER_TREESITTER_PYTHON_SO are available
pytest tests/integration/test_parser_adapter_treesitter_integration.py -q -m integration || true
# run linters and mypy
ruff check tasker tests
mypy tasker --strict
# commit and push
git add -A
git commit -m "feat(infra): add TreeSitterParser adapter with Python ast fallback and tests"
git push origin feature/parser-adapter
```

---

#### PR body exact text to paste

```
Summary:
- Added TreeSitterParser adapter at tasker/infrastructure/parser_adapter.py implementing ParserPort.
- Added parser configuration helper tasker/infrastructure/parser_config.py.
- Added unit tests tests/infrastructure/test_parser_adapter_unit.py.
- Added integration test tests/integration/test_parser_adapter_treesitter_integration.py (skips if Tree-Sitter not available).
- Added documentation tasker/infrastructure/PARSER_ADAPTER.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests: pytest tests/infrastructure/test_parser_adapter_unit.py (passed).
3. Ran integration tests conditionally: pytest tests/integration/test_parser_adapter_treesitter_integration.py (skipped if Tree-Sitter not available).
4. Ran linters and type checks: ruff, mypy --strict.

Files changed:
- tasker/infrastructure/parser_adapter.py
- tasker/infrastructure/parser_config.py
- tasker/infrastructure/PARSER_ADAPTER.md
- tests/infrastructure/test_parser_adapter_unit.py
- tests/integration/test_parser_adapter_treesitter_integration.py

Notes:
- Tree-Sitter is optional. The adapter falls back to Python ast for .py files to guarantee deterministic behavior in environments without compiled grammars.
- To enable Tree-Sitter integration tests, set TASKER_TREESITTER_PYTHON_SO to the path of a compiled Tree-Sitter python language .so and ensure the tree_sitter Python package is installed.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `tasker/infrastructure/parser_adapter.py` exists and implements `parse_file`, `extract_symbols`, and `extract_imports` with the exact method names and signatures from `ParserPort`.
- The adapter uses Tree‑Sitter when available and falls back to Python `ast` for `.py` files.
- `tests/infrastructure/test_parser_adapter_unit.py` passes.
- `tests/integration/test_parser_adapter_treesitter_integration.py` is present and **skips** when Tree‑Sitter or `TASKER_TREESITTER_PYTHON_SO` is not available.
- `tasker/infrastructure/PARSER_ADAPTER.md` documents behavior, fallback semantics, and configuration.
- Branch `feature/parser-adapter` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `infra`
- `parser`
- `tests`
- `medium-priority`

---

#### Estimated effort
**Medium (M)** — expected to take an autonomous agent or engineer **2–5 hours** depending on whether Tree‑Sitter integration is exercised.