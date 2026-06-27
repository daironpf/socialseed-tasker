"""Parser configuration - supported extensions and Tree-Sitter grammar paths."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ParserConfig:
    """Configuration for the TreeSitterParser adapter.

    Attributes:
        supported_extensions: List of file extensions to parse (e.g. [".py", ".js"]).
        treesitter_python_so: Optional path to compiled Tree-Sitter Python grammar .so file.
    """

    supported_extensions: list[str]
    treesitter_python_so: str | None

    @staticmethod
    def load_from_env() -> ParserConfig:
        exts = os.getenv("TASKER_PARSER_EXTENSIONS", ".py").split(",")
        exts = [e.strip() if e.strip().startswith(".") else f".{e.strip()}" for e in exts if e.strip()]
        ts_so = os.getenv("TASKER_TREESITTER_PYTHON_SO")
        return ParserConfig(supported_extensions=exts, treesitter_python_so=ts_so)
