"""Code Graph Entities - AST nodes for code-as-graph feature.

These entities represent the graph structure of parsed source code,
enabling AI agents to understand code relationships and dependencies.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SymbolType(str, Enum):
    """Types of code symbols that can be extracted from AST."""

    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    IMPORT = "import"
    VARIABLE = "variable"
    CONSTANT = "constant"
    TEST = "test"


class CodeFile(BaseModel):
    """A source code file in the graph.

    Represents a file that has been parsed and added to the code graph.
    Contains metadata about the file including language, size, and location.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    path: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    lines_of_code: int = Field(default=0, ge=0)
    file_hash: str | None = None
    commit_sha: str | None = None
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    repository_path: str | None = None


class CodeSymbol(BaseModel):
    """A code symbol (class, function, method, variable) in the graph.

    Represents a named element in the source code with its location
    and metadata.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1)
    symbol_type: SymbolType
    file_id: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_column: int = Field(ge=0)
    end_column: int = Field(ge=0)
    parameters: list[str] = Field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = Field(default_factory=list)
    is_test: bool = False
    parent_symbol_id: str | None = None


class CodeImport(BaseModel):
    """An import statement in the code graph.

    Represents a dependency or import from another module.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    file_id: str
    module: str
    names: list[str] = Field(default_factory=list)
    alias: str | None = None
    line_number: int = Field(ge=1)
    is_from: bool = False


class RelationshipType(str, Enum):
    """Types of relationships between code elements."""

    CALLS = "calls"
    DEFINES = "defines"
    DEPENDS_ON = "depends_on"
    TESTS = "tests"
    CONTAINS = "contains"
    IMPORTS = "imports"


class CodeRelationship(BaseModel):
    """A relationship between two code elements in the graph.

    Represents how different code elements (files, functions, classes) relate
    to each other (e.g., calls, depends_on, tests).
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    commit_sha: str | None = None


class CodeGraphStats(BaseModel):
    """Statistics about the code graph."""

    total_files: int = 0
    total_symbols: int = 0
    total_relationships: int = 0
    by_language: dict[str, int] = Field(default_factory=dict)
    by_symbol_type: dict[SymbolType, int] = Field(default_factory=dict)
    last_scan: datetime | None = None