"""Unit tests for Code-as-Graph parser and entities."""

import pytest
from pathlib import Path

from socialseed_tasker.core.code_analysis.entities import (
    CodeFile,
    CodeImport,
    CodeRelationship,
    CodeSymbol,
    RelationshipType,
    SymbolType,
)


class TestCodeFileEntity:
    """Tests for CodeFile entity."""

    def test_create_code_file(self):
        """Test creating a CodeFile entity."""
        file = CodeFile(
            path="src/main.py",
            language="python",
            lines_of_code=100,
        )

        assert file.path == "src/main.py"
        assert file.language == "python"
        assert file.lines_of_code == 100
        assert file.id is not None

    def test_code_file_with_all_fields(self):
        """Test creating a CodeFile with all fields."""
        file = CodeFile(
            path="src/utils/helper.py",
            language="python",
            lines_of_code=50,
            file_hash="abc123",
            commit_sha="def456",
            repository_path="/repo",
        )

        assert file.file_hash == "abc123"
        assert file.commit_sha == "def456"
        assert file.repository_path == "/repo"


class TestCodeSymbolEntity:
    """Tests for CodeSymbol entity."""

    def test_create_code_symbol(self):
        """Test creating a CodeSymbol entity."""
        symbol = CodeSymbol(
            name="MyClass",
            symbol_type=SymbolType.CLASS,
            file_id="file-123",
            start_line=10,
            end_line=20,
            start_column=0,
            end_column=10,
        )

        assert symbol.name == "MyClass"
        assert symbol.symbol_type == SymbolType.CLASS
        assert symbol.file_id == "file-123"
        assert symbol.start_line == 10

    def test_code_symbol_function(self):
        """Test creating a function symbol."""
        symbol = CodeSymbol(
            name="process_data",
            symbol_type=SymbolType.FUNCTION,
            file_id="file-123",
            start_line=5,
            end_line=15,
            start_column=0,
            end_column=20,
            parameters=["data", "options"],
            return_type="dict",
        )

        assert symbol.parameters == ["data", "options"]
        assert symbol.return_type == "dict"

    def test_code_symbol_test(self):
        """Test creating a test symbol."""
        symbol = CodeSymbol(
            name="test_process_data",
            symbol_type=SymbolType.FUNCTION,
            file_id="file-123",
            start_line=1,
            end_line=10,
            start_column=0,
            end_column=15,
            is_test=True,
        )

        assert symbol.is_test is True


class TestCodeImportEntity:
    """Tests for CodeImport entity."""

    def test_create_code_import(self):
        """Test creating a CodeImport entity."""
        imp = CodeImport(
            file_id="file-123",
            module="os.path",
            names=["join"],
            line_number=5,
            is_from=True,
        )

        assert imp.module == "os.path"
        assert imp.names == ["join"]
        assert imp.is_from is True

    def test_create_simple_import(self):
        """Test creating a simple import."""
        imp = CodeImport(
            file_id="file-123",
            module="json",
            line_number=3,
            is_from=False,
        )

        assert imp.is_from is False
        assert imp.names == []


class TestCodeRelationshipEntity:
    """Tests for CodeRelationship entity."""

    def test_create_code_relationship(self):
        """Test creating a CodeRelationship entity."""
        rel = CodeRelationship(
            source_id="src-123",
            target_id="tgt-456",
            relationship_type=RelationshipType.CALLS,
        )

        assert rel.source_id == "src-123"
        assert rel.target_id == "tgt-456"
        assert rel.relationship_type == RelationshipType.CALLS

    def test_all_relationship_types(self):
        """Test all relationship types."""
        for rel_type in RelationshipType:
            rel = CodeRelationship(
                source_id="src-1",
                target_id="tgt-1",
                relationship_type=rel_type,
            )
            assert rel.relationship_type == rel_type


class TestParserBasics:
    """Tests for CodeGraphParser basic functionality."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        assert parser is not None

    def test_language_detection(self):
        """Test language detection from file extension."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()

        from pathlib import Path

        assert parser._detect_language(Path("main.py")) == "python"
        assert parser._detect_language(Path("app.js")) == "javascript"
        assert parser._detect_language(Path("app.ts")) == "typescript"
        assert parser._detect_language(Path("main.go")) == "go"
        assert parser._detect_language(Path("lib.rs")) == "rust"
        assert parser._detect_language(Path("main.java")) == "java"
        assert parser._detect_language(Path("unknown.xyz")) == "unknown"

    def test_source_file_iteration(self):
        """Test source file iteration."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()

        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "src"))
            os.makedirs(os.path.join(tmpdir, "tests"))

            Path(os.path.join(tmpdir, "src", "main.py")).write_text("print('hello')")
            Path(os.path.join(tmpdir, "tests", "test_main.py")).write_text("def test(): pass")
            Path(os.path.join(tmpdir, "README.md")).write_text("# Readme")

            files = parser._iter_source_files(Path(tmpdir))

            assert len(files) == 2
            paths = [str(f) for f in files]
            assert any("main.py" in p for p in paths)
            assert any("test_main.py" in p for p in paths)
            assert not any("README.md" in p for p in paths)


class TestSymbolTypes:
    """Tests for SymbolType enum."""

    def test_all_symbol_types(self):
        """Test all symbol types exist."""
        assert SymbolType.FILE.value == "file"
        assert SymbolType.CLASS.value == "class"
        assert SymbolType.FUNCTION.value == "function"
        assert SymbolType.METHOD.value == "method"
        assert SymbolType.IMPORT.value == "import"
        assert SymbolType.VARIABLE.value == "variable"
        assert SymbolType.CONSTANT.value == "constant"
        assert SymbolType.TEST.value == "test"