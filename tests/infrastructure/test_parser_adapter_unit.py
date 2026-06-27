"""Unit tests for TreeSitterParser using Python ast fallback."""

import textwrap

from socialseed_tasker.application.exceptions import ParserError
from socialseed_tasker.infrastructure.parser_adapter import TreeSitterParser
from socialseed_tasker.infrastructure.parser_config import ParserConfig

PY_SIMPLE = textwrap.dedent("""\
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
    names = {s["name"] for s in symbols if "name" in s}
    assert "Foo" in names or any("Foo" in str(s) for s in names)
    assert "bar" in names or any("bar" in str(s) for s in names)
    imports = parser.extract_imports(ast_dict)
    assert "os" in imports or "sys" in imports or "math" in imports


def test_parse_nonexistent_file_raises():
    config = ParserConfig(supported_extensions=[".py"], treesitter_python_so=None)
    parser = TreeSitterParser(config=config)
    try:
        parser.parse_file("/path/does/not/exist.py")
        raise AssertionError("Expected ParserError")
    except ParserError:
        pass


def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "file.js"
    p.write_text("var x = 1;", encoding="utf-8")
    config = ParserConfig(supported_extensions=[".py"], treesitter_python_so=None)
    parser = TreeSitterParser(config=config)
    try:
        parser.parse_file(str(p))
        raise AssertionError("Expected ParserError")
    except ParserError:
        pass


def test_empty_file_returns_dict(tmp_path):
    p = tmp_path / "empty.py"
    p.write_text("", encoding="utf-8")
    config = ParserConfig(supported_extensions=[".py"], treesitter_python_so=None)
    parser = TreeSitterParser(config=config)
    ast_dict = parser.parse_file(str(p))
    assert isinstance(ast_dict, dict)
    imports = parser.extract_imports(ast_dict)
    assert imports == []


def test_class_without_methods_still_extracted(tmp_path):
    p = tmp_path / "empty_class.py"
    p.write_text("class Empty: pass", encoding="utf-8")
    config = ParserConfig(supported_extensions=[".py"], treesitter_python_so=None)
    parser = TreeSitterParser(config=config)
    ast_dict = parser.parse_file(str(p))
    symbols = parser.extract_symbols(ast_dict)
    assert any(s.get("type") == "class" for s in symbols)
