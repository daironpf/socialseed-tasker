"""Deterministic fake ParserPort for domain-level tests (no infrastructure)."""

from __future__ import annotations

from socialseed_tasker.application.ports import ParserPort


class FakeParser(ParserPort):
    """Returns deterministic AST, symbols, and imports for every input."""

    def parse_file(self, path: str) -> dict:
        return {"type": "file", "path": path, "children": []}

    def extract_symbols(self, ast: dict) -> list[dict]:
        return [{"name": "fake_symbol", "type": "function"}]

    def extract_imports(self, ast: dict) -> list[str]:
        return ["fake_import"]
