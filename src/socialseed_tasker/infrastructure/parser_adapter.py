"""TreeSitterParser adapter implementing ParserPort with Python ast fallback.

Uses Tree-Sitter when available and falls back to Python's builtin ``ast``
for ``.py`` files when Tree-Sitter is not available or initialization fails.
"""

from __future__ import annotations

import ast as py_ast
import os
from typing import Any

from socialseed_tasker.application.exceptions import ParserError
from socialseed_tasker.application.ports import ParserPort
from socialseed_tasker.observability.logging import get_logger
from socialseed_tasker.observability.metrics import observe_operation

try:
    from tree_sitter import Language, Parser  # type: ignore[import-untyped]

    _TREE_SITTER_AVAILABLE = True
except Exception:
    _TREE_SITTER_AVAILABLE = False

from socialseed_tasker.infrastructure.parser_config import ParserConfig


class TreeSitterParser(ParserPort):
    """Parser adapter that uses Tree-Sitter when available and falls back to Python's ast for .py files.

    Behavior:
    - parse_file(path) returns a deterministic AST-like dict with keys:
      { "type": "<node-type>", "start_byte": int, "end_byte": int, "text": str, "children": [ ... ] }
    - extract_symbols(ast_dict) returns a list of symbol descriptors:
      [ {"name": str, "type": "function"|"class"|"variable", "location": {"start": int, "end": int}} ]
    - extract_imports(ast_dict) returns a list of import targets as strings.
    - On unreadable files or unsupported extensions, raise ParserError.
    """

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig.load_from_env()
        self.logger = get_logger("tasker.parser")
        self._ts_parser = None
        self._ts_language = None
        if _TREE_SITTER_AVAILABLE and self.config.treesitter_python_so:
            try:
                self._ts_language = Language(self.config.treesitter_python_so, "python")
                p = Parser()
                p.set_language(self._ts_language)
                self._ts_parser = p
            except Exception:
                self._ts_parser = None
                self._ts_language = None

    def parse_file(self, path: str) -> dict[str, Any]:
        with observe_operation("parser", "parse_file"):
            self.logger.info("parser.parse_file.start", extra={"path": path})
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

            if self._ts_parser and ext == ".py":
                try:
                    tree = self._ts_parser.parse(raw)
                    root = tree.root_node
                    return self._node_to_dict(root, raw)
                except Exception:
                    pass

            if ext == ".py":
                try:
                    text = raw.decode("utf-8")
                    py_tree = py_ast.parse(text)
                    return self._ast_to_dict(py_tree, text)
                except Exception as exc:
                    raise ParserError(f"Python AST parse failed for {path}: {exc}") from exc

            raise ParserError(f"No parser available for extension: {ext}")

    def extract_symbols(self, ast_dict: dict[str, Any]) -> list[dict[str, Any]]:
        symbols: list[dict[str, Any]] = []
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
            elif ntype in ("assignment", "assign"):
                targets = node.get("targets") or []
                for t in targets:
                    if isinstance(t, dict) and "name" in t:
                        symbols.append({"name": t["name"], "type": "variable", "location": t.get("location")})
            children = node.get("children") or []
            for c in children:
                stack.append(c)
        return symbols

    def extract_imports(self, ast_dict: dict[str, Any]) -> list[str]:
        imports: list[str] = []
        stack = [ast_dict]
        while stack:
            node = stack.pop()
            ntype = node.get("type")
            if ntype in ("import_statement", "import_from", "import"):
                module = node.get("module") or node.get("module_name") or node.get("text")
                if isinstance(module, str):
                    imports.append(module.strip())
                else:
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

    def _node_to_dict(self, node, raw_bytes: bytes) -> dict[str, Any]:
        text = raw_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
        d: dict[str, Any] = {
            "type": node.type,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
            "text": text,
            "children": [],
            "location": {"start": node.start_byte, "end": node.end_byte},
        }
        try:
            name_node = None
            for child in node.children:
                if child.type == "identifier":
                    name_node = child
                    break
            if name_node:
                d["name"] = raw_bytes[name_node.start_byte : name_node.end_byte].decode("utf-8", errors="replace")
        except Exception:
            pass
        for c in node.children:
            d["children"].append(self._node_to_dict(c, raw_bytes))
        if node.type in ("assignment", "assign"):
            targets = []
            for c in node.children:
                if c.type == "identifier":
                    targets.append(
                        {
                            "name": raw_bytes[c.start_byte : c.end_byte].decode("utf-8", errors="replace"),
                            "location": {"start": c.start_byte, "end": c.end_byte},
                        }
                    )
            if targets:
                d["targets"] = targets
        return d

    def _ast_to_dict(self, node: py_ast.AST, source_text: str) -> dict[str, Any]:
        def _node(n: py_ast.AST) -> dict[str, Any]:
            d: dict[str, Any] = {
                "type": type(n).__name__,
                "children": [],
                "text": "",
                "location": {},
            }
            if hasattr(n, "lineno") and hasattr(n, "end_lineno"):
                try:
                    start = n.lineno
                    end = n.end_lineno
                    d["location"] = {"start_line": start, "end_line": end}
                except Exception:
                    d["location"] = {}
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
            if isinstance(n, py_ast.Import):
                names = [alias.name for alias in n.names]
                d["type"] = "import_statement"
                d["names"] = names
            if isinstance(n, py_ast.ImportFrom):
                module = n.module or ""
                d["type"] = "import_from"
                d["module"] = module
                d["names"] = [alias.name for alias in n.names]
            try:
                if hasattr(n, "lineno") and hasattr(n, "end_lineno"):
                    lines = source_text.splitlines()
                    s = max(0, n.lineno - 1)
                    e = min(len(lines), n.end_lineno)
                    d["text"] = "\n".join(lines[s:e])
            except Exception:
                d["text"] = ""
            for child in py_ast.iter_child_nodes(n):
                d["children"].append(_node(child))
            return d

        return _node(node)
