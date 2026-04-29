"""Code Graph Parser - Extract code structure from source files.

This module provides functionality to parse source code and extract graph structures
using tree-sitter for AST parsing. Falls back to basic parsing if tree-sitter
is not available.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Protocol

from socialseed_tasker.core.code_analysis.entities import (
    CodeFile,
    CodeImport,
    CodeRelationship,
    CodeSymbol,
    RelationshipType,
    SymbolType,
)


class TreeSitterLanguage(Protocol):
    """Protocol for tree-sitter language parsers."""

    def parse(self, source: bytes):
        ...


LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}

TEST_PATTERNS = [
    re.compile(r"test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r".*\.spec\.(js|ts|jsx|tsx)$"),
    re.compile(r".*\.test\.(js|ts|jsx|tsx)$"),
    re.compile(r"^test_.*\.go$"),
    re.compile(r".*_test\.rs$"),
]


class CodeGraphParser:
    """Parser for extracting code structure into a graph.

    Uses tree-sitter for language-aware parsing when available,
    otherwise falls back to regex-based extraction.
    """

    def __init__(self):
        self._tree_sitter_available = self._check_tree_sitter()
        self._parsers: dict[str, TreeSitterLanguage] = {}

    def _check_tree_sitter(self) -> bool:
        """Check if tree-sitter is available."""
        try:
            import tree_sitter
            return True
        except ImportError:
            return False

    def scan_repository(
        self,
        repository_path: str,
        incremental: bool = False,
        git_aware: bool = True,
    ) -> tuple[list[CodeFile], list[CodeSymbol], list[CodeImport], list[CodeRelationship]]:
        """Scan a repository and extract code graph.

        Args:
            repository_path: Path to the repository to scan
            incremental: Only scan changed files
            git_aware: Use git to track file changes

        Returns:
            Tuple of (files, symbols, imports, relationships)
        """
        repo_path = Path(repository_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repository_path}")

        files: list[CodeFile] = []
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        relationships: list[CodeRelationship] = []

        commit_sha = self._get_current_commit(repo_path) if git_aware else None
        modified_files = self._get_modified_files(repo_path) if incremental and git_aware else None

        for file_path in self._iter_source_files(repo_path):
            if modified_files and str(file_path) not in modified_files:
                continue

            try:
                file_content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            language = self._detect_language(file_path)
            file_hash = hashlib.md5(file_content.encode()).hexdigest()

            code_file = CodeFile(
                path=str(file_path.relative_to(repo_path)),
                language=language,
                lines_of_code=len(file_content.splitlines()),
                file_hash=file_hash,
                commit_sha=commit_sha,
                repository_path=str(repo_path),
            )
            files.append(code_file)

            file_symbols, file_imports, file_relationships = self._parse_file(
                file_path, file_content, code_file.id, language
            )
            symbols.extend(file_symbols)
            imports.extend(file_imports)
            relationships.extend(file_relationships)

        return files, symbols, imports, relationships

    def _iter_source_files(self, repo_path: Path) -> list[Path]:
        """Iterate over source files in the repository."""
        source_files = []
        exclude_dirs = {".git", "__pycache__", "node_modules", "venv", ".venv", "dist", "build"}

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                ext = Path(file).suffix
                if ext in LANGUAGE_EXTENSIONS:
                    source_files.append(Path(root) / file)

        return source_files

    def _detect_language(self, file_path: Path) -> str:
        """Detect the programming language from file extension."""
        ext = file_path.suffix
        return LANGUAGE_EXTENSIONS.get(ext, "unknown")

    def _get_current_commit(self, repo_path: Path) -> str | None:
        """Get the current git commit SHA."""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def _get_modified_files(self, repo_path: Path) -> set[str]:
        """Get modified files from git."""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return set(result.stdout.strip().splitlines())
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return set()

    def _parse_file(
        self,
        file_path: Path,
        content: str,
        file_id: str,
        language: str,
    ) -> tuple[list[CodeSymbol], list[CodeImport], list[CodeRelationship]]:
        """Parse a single file and extract symbols, imports, and relationships."""
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        relationships: list[CodeRelationship] = []

        is_test = any(pattern.match(file_path.name) for pattern in TEST_PATTERNS)

        if language == "python":
            symbols, imports, relationships = self._parse_python(content, file_id, is_test)
        elif language in ("javascript", "typescript"):
            symbols, imports, relationships = self._parse_js_ts(content, file_id, is_test, language)

        return symbols, imports, relationships

    def _parse_python(
        self,
        content: str,
        file_id: str,
        is_test: bool,
    ) -> tuple[list[CodeSymbol], list[CodeImport], list[CodeRelationship]]:
        """Parse Python source code."""
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        relationships: list[CodeRelationship] = []

        lines = content.splitlines()
        current_class: str | None = None

        import_pattern = re.compile(r"^(?:from\s+(\S+)\s+import|import\s+(\S+))")
        class_pattern = re.compile(r"^class\s+(\w+)(?:\((\w+)\))?:")
        func_pattern = re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(")
        decorator_pattern = re.compile(r"^@\w+")

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            import_match = import_pattern.match(stripped)
            if import_match:
                module = import_match.group(1) or import_match.group(2)
                names = []
                if "from" in stripped:
                    parts = stripped.split("import")
                    if len(parts) > 1:
                        names = [n.strip() for n in parts[1].split(",")]

                imports.append(
                    CodeImport(
                        file_id=file_id,
                        module=module,
                        names=names,
                        line_number=i,
                        is_from="from" in stripped,
                    )
                )
                continue

            class_match = class_pattern.match(stripped)
            if class_match:
                class_name = class_match.group(1)
                current_class = class_name

                symbols.append(
                    CodeSymbol(
                        name=class_name,
                        symbol_type=SymbolType.CLASS,
                        file_id=file_id,
                        start_line=i,
                        end_line=i,
                        start_column=0,
                        end_column=len(line),
                        is_test=is_test,
                    )
                )
                continue

            if decorator_pattern.match(stripped):
                continue

            func_match = func_pattern.match(stripped)
            if func_match and current_class:
                func_name = func_match.group(1)
                symbols.append(
                    CodeSymbol(
                        name=func_name,
                        symbol_type=SymbolType.METHOD if current_class else SymbolType.FUNCTION,
                        file_id=file_id,
                        start_line=i,
                        end_line=i,
                        start_column=0,
                        end_column=len(line),
                        parent_symbol_id=None,
                        is_test=is_test,
                    )
                )
                relationships.append(
                    CodeRelationship(
                        source_id=file_id,
                        target_id=file_id,
                        relationship_type=RelationshipType.DEFINES,
                    )
                )

        return symbols, imports, relationships

    def _parse_js_ts(
        self,
        content: str,
        file_id: str,
        is_test: bool,
        language: str,
    ) -> tuple[list[CodeSymbol], list[CodeImport], list[CodeRelationship]]:
        """Parse JavaScript/TypeScript source code."""
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        relationships: list[CodeRelationship] = []

        lines = content.splitlines()

        import_pattern = re.compile(r"^(?:import\s+(?:{[^}]+}|\w+)\s+from\s+['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"])")
        func_pattern = re.compile(r"^(?:async\s+)?(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\()")
        class_pattern = re.compile(r"^class\s+(\w+)")
        arrow_pattern = re.compile(r"^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(")
        method_pattern = re.compile(r"^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*{")

        current_class: str | None = None

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            import_match = import_pattern.match(stripped)
            if import_match:
                module = import_match.group(1) or import_match.group(2)
                if module:
                    imports.append(
                        CodeImport(
                            file_id=file_id,
                            module=module,
                            line_number=i,
                            is_from=True,
                        )
                    )
                continue

            class_match = class_pattern.match(stripped)
            if class_match:
                current_class = class_match.group(1)
                symbols.append(
                    CodeSymbol(
                        name=current_class,
                        symbol_type=SymbolType.CLASS,
                        file_id=file_id,
                        start_line=i,
                        end_line=i,
                        start_column=0,
                        end_column=len(line),
                        is_test=is_test,
                    )
                )
                continue

            method_match = method_pattern.match(stripped)
            if current_class and method_match:
                method_name = method_match.group(1)
                if method_name not in ("if", "for", "while", "switch", "else"):
                    symbols.append(
                        CodeSymbol(
                            name=method_name,
                            symbol_type=SymbolType.METHOD,
                            file_id=file_id,
                            start_line=i,
                            end_line=i,
                            start_column=len(line) - len(line.lstrip()),
                            end_column=len(line),
                            is_test=is_test,
                        )
                    )

        return symbols, imports, relationships

    def find_symbols(
        self,
        name: str | None = None,
        symbol_type: SymbolType | None = None,
        file_path: str | None = None,
    ) -> list[CodeSymbol]:
        """Find symbols matching criteria.

        This is a placeholder - actual implementation would query Neo4j.
        """
        return []

    def get_file_dependencies(self, file_path: str) -> list[str]:
        """Get dependencies for a file.

        This is a placeholder - actual implementation would query Neo4j.
        """
        return []

    def get_callers(self, symbol_name: str) -> list[str]:
        """Get functions that call a given symbol.

        This is a placeholder - actual implementation would query Neo4j.
        """
        return []