"""Issue #585: every ``$param`` in ``neo4j_queries.py`` must match the kwargs of
its call-sites, under a single snake_case convention.

The audit that found the bug family was a one-off script; this test pins the
pairing forever. It parses the queries module with ``ast`` and every
``queries.NAME`` / ``neo4j_queries.NAME`` call in ``src/`` (including multiline
kwargs, positional param dicts and ``**dict`` spreads of known helpers).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
QUERIES_FILE = SRC / "socialseed_tasker" / "infrastructure" / "neo4j_queries.py"
CAMEL_PARAM = re.compile(r"\$[a-z]+[A-Z]")


def _literal_string(node: ast.AST) -> str | None:
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return None
    return value if isinstance(value, str) else None


def _load_queries() -> dict[str, set[str]]:
    tree = ast.parse(QUERIES_FILE.read_text(encoding="utf-8"))
    queries: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.isupper():
            continue
        text = _literal_string(node.value)
        if text is None:
            continue
        queries[target.id] = set(re.findall(r"\$([A-Za-z_][A-Za-z0-9_]*)", text))
    return queries


def _dict_keys(node: ast.Dict) -> set[str]:
    return {
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


def _module_dict_assignments(tree: ast.AST) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Dict)
        ):
            found[node.targets[0].id] = _dict_keys(node.value)
    return found


def _helper_dict_returns(tree: ast.AST) -> dict[str, set[str]]:
    """Keys of ``return {...}`` inside module-level helpers (e.g. _policy_to_dict)."""
    found: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                found[node.name] = _dict_keys(child.value)
    return found


def _call_kwargs(node: ast.Call, dict_vars: dict[str, set[str]], helpers: dict[str, set[str]]) -> set[str] | None:
    """Kwargs provided at a ``queries.NAME`` call. ``None`` means unresolved."""
    kwargs: set[str] = set()
    for kw in node.keywords:
        if kw.arg is not None:
            kwargs.add(kw.arg)
            continue
        value = kw.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in helpers:
            kwargs |= helpers[value.func.id]
        else:
            return None  # unknown **spread
    for arg in node.args[1:]:  # args[0] is the query itself
        if isinstance(arg, ast.Dict):
            kwargs |= _dict_keys(arg)
        elif isinstance(arg, ast.Name) and arg.id in dict_vars:
            kwargs |= dict_vars[arg.id]
        else:
            return None
    return kwargs


def _iter_query_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in ("queries", "neo4j_queries")
        ):
            yield node, func.attr


def test_no_camelcase_params_in_queries_module() -> None:
    """Single convention: no ``$camelCase`` token may survive in neo4j_queries.py."""
    text = QUERIES_FILE.read_text(encoding="utf-8")
    leftovers = sorted(set(CAMEL_PARAM.findall(text)))
    assert leftovers == [], f"camelCase $params still present: {leftovers}"


def test_query_params_match_call_site_kwargs() -> None:
    queries = _load_queries()
    assert len(queries) > 100, f"expected the full query catalogue, got {len(queries)}"

    mismatches: list[str] = []
    for py_file in sorted(SRC.rglob("*.py")):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        dict_vars = _module_dict_assignments(tree)
        helpers = _helper_dict_returns(tree)
        for node, qname in _iter_query_calls(tree):
            required = queries.get(qname)
            if required is None:
                mismatches.append(f"{py_file.name}:{node.lineno}: unknown query {qname}")
                continue
            kwargs = _call_kwargs(node, dict_vars, helpers)
            if kwargs is None:
                continue  # documented dynamic call-site, reviewed for #585
            missing = sorted(required - kwargs)
            if missing:
                rel = py_file.relative_to(SRC)
                mismatches.append(f"{rel}:{node.lineno}: {qname} missing {missing}")

    assert mismatches == [], "query $params vs call-site kwargs mismatch:\n" + "\n".join(mismatches)
