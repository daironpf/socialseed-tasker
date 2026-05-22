"""Integration tests for TreeSitterParser using the Tree-Sitter branch.

Skips if tree_sitter is not importable or TASKER_TREESITTER_PYTHON_SO is not set.
"""

import os

import pytest

from socialseed_tasker.infrastructure.parser_adapter import TreeSitterParser
from socialseed_tasker.infrastructure.parser_config import ParserConfig

try:
    from tree_sitter import Language  # type: ignore[import-untyped]

    _TS_AVAILABLE = True
except Exception:
    _TS_AVAILABLE = False

pytestmark = pytest.mark.integration


def _skip_if_no_treesitter():
    if not _TS_AVAILABLE or not os.getenv("TASKER_TREESITTER_PYTHON_SO"):
        pytest.skip("Tree-Sitter not available or TASKER_TREESITTER_PYTHON_SO not set")


def test_treesitter_python_parse(tmp_path):
    _skip_if_no_treesitter()
    sample = tmp_path / "sample.py"
    sample.write_text("def f():\n    return 1\n", encoding="utf-8")
    config = ParserConfig(
        supported_extensions=[".py"],
        treesitter_python_so=os.getenv("TASKER_TREESITTER_PYTHON_SO"),
    )
    parser = TreeSitterParser(config=config)
    ast_dict = parser.parse_file(str(sample))
    assert isinstance(ast_dict, dict)
    symbols = parser.extract_symbols(ast_dict)
    assert any(s.get("type") == "function" or s.get("name") == "f" for s in symbols)
