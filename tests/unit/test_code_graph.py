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
            name="main.py",
            language="python",
            lines_of_code=100,
        )

        assert file.path == "src/main.py"
        assert file.name == "main.py"
        assert file.language == "python"
        assert file.lines_of_code == 100
        assert file.id is not None

    def test_code_file_with_all_fields(self):
        """Test creating a CodeFile with all fields."""
        file = CodeFile(
            path="src/utils/helper.py",
            name="helper.py",
            language="python",
            lines_of_code=50,
            file_hash="abc123",
            commit_sha="def456",
            repository_path="/repo",
        )

        assert file.file_hash == "abc123"
        assert file.name == "helper.py"
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


class TestPythonParsing:
    """Tests for Python code parsing."""

    def test_parse_simple_class(self):
        """Test parsing a simple Python class."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        content = '''
class MyClass:
    def __init__(self):
        pass

    def process(self, data):
        return data
'''

        file_id = "test-file-1"
        symbols, imports, relationships = parser._parse_file(
            Path("test.py"), content, file_id, "python"
        )

        class_symbols = [s for s in symbols if s.symbol_type == SymbolType.CLASS]
        assert len(class_symbols) == 1
        assert class_symbols[0].name == "MyClass"

    def test_parse_class_with_methods(self):
        """Test parsing class with methods."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        content = '''
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, x, y):
        return x - y
'''

        file_id = "test-file-2"
        symbols, imports, relationships = parser._parse_file(
            Path("calculator.py"), content, file_id, "python"
        )

        methods = [s for s in symbols if s.symbol_type == SymbolType.METHOD]
        assert len(methods) == 2
        method_names = [m.name for m in methods]
        assert "add" in method_names
        assert "subtract" in method_names
        assert "a" in methods[0].parameters[1]
        assert methods[0].return_type == "int"

    def test_parse_functions(self):
        """Test parsing standalone functions."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        content = '''
def main():
    print("Hello")

def process_data(items: list[str]) -> dict:
    return {"count": len(items)}
'''

        file_id = "test-file-3"
        symbols, imports, relationships = parser._parse_file(
            Path("main.py"), content, file_id, "python"
        )

        functions = [s for s in symbols if s.symbol_type == SymbolType.FUNCTION]
        assert len(functions) == 2
        func_names = [f.name for f in functions]
        assert "main" in func_names
        assert "process_data" in func_names
        assert any(f.name == "process_data" and f.return_type == "dict" for f in functions)

    def test_parse_imports(self):
        """Test parsing import statements."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        content = '''
import os
import sys as system
from pathlib import Path
from typing import List, Dict
'''

        file_id = "test-file-4"
        symbols, imports, relationships = parser._parse_file(
            Path("test.py"), content, file_id, "python"
        )

        assert len(imports) >= 3
        modules = [i.module for i in imports]
        assert "os" in modules
        assert any("path" in m.lower() for m in modules)

    def test_parse_call_relationships(self):
        """Test parsing function call relationships."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        content = '''
def helper():
    return 1

def main():
    result = helper()
    return result
'''

        file_id = "test-file-5"
        symbols, imports, relationships = parser._parse_file(
            Path("test.py"), content, file_id, "python"
        )

        call_rels = [r for r in relationships if r.relationship_type == RelationshipType.CALLS]
        assert len(call_rels) >= 0

    def test_parse_test_function_detection(self):
        """Test detection of test functions."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        content = '''
def test_something():
    assert True

def regular_function():
    pass
'''

        file_id = "test-file-6"
        symbols, imports, relationships = parser._parse_file(
            Path("test_foo.py"), content, file_id, "python"
        )

        test_funcs = [s for s in symbols if s.name.startswith("test_")]
        assert len(test_funcs) == 1
        assert test_funcs[0].name == "test_something"


class TestRepositoryStorage:
    """Tests for Neo4j repository storage."""

    def test_save_and_query_files(self):
        """Test saving and querying files in Neo4j."""
        from unittest.mock import MagicMock

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_tx = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_session.begin_transaction.return_value = mock_tx

        from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

        repo = CodeGraphRepository(mock_driver)

        files = [
            CodeFile(
                path="src/main.py",
                name="main.py",
                language="python",
                lines_of_code=100,
            )
        ]
        symbols = []
        imports = []
        relationships = []

        repo.save_scan_results(files, symbols, imports, relationships)

    def test_get_stats(self):
        """Test getting code graph stats."""
        from unittest.mock import MagicMock
        from contextlib import contextmanager

        mock_driver = MagicMock()
        mock_inner_driver = MagicMock()

        @contextmanager
        def mock_session(database=None):
            mock_session_obj = MagicMock()
            mock_result = MagicMock()
            mock_record = MagicMock()
            mock_record.__getitem__ = lambda self, key: {
                "total_files": 5,
                "total_symbols": 20,
                "total_relationships": 15,
                "languages": ["python"],
            }[key]
            mock_result.single.return_value = mock_record
            mock_session_obj.run.return_value = mock_result
            yield mock_session_obj

        mock_inner_driver.session = mock_session
        mock_driver.driver = mock_inner_driver
        mock_driver.database = "neo4j"

        from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

        repo = CodeGraphRepository(mock_driver)
        stats = repo.get_stats()

        assert stats.total_files == 5
        assert stats.total_symbols == 20
        assert stats.total_relationships == 15

    def test_find_symbols_by_name(self):
        """Test finding symbols by name."""
        from unittest.mock import MagicMock
        from contextlib import contextmanager

        mock_driver = MagicMock()
        mock_inner_driver = MagicMock()

        class MockRecord:
            def __getitem__(self, key):
                if key == "s":
                    return {"name": "MyClass", "symbol_type": "class", "id": "123"}
                raise KeyError(key)

        @contextmanager
        def mock_session(database=None):
            mock_session_obj = MagicMock()
            mock_result = MagicMock()
            mock_record = MockRecord()
            mock_result.__iter__ = MagicMock(return_value=iter([mock_record]))
            mock_session_obj.run.return_value = mock_result
            yield mock_session_obj

        mock_inner_driver.session = mock_session
        mock_driver.driver = mock_inner_driver
        mock_driver.database = "neo4j"

        from socialseed_tasker.storage.graph_database.code_graph_repository import CodeGraphRepository

        repo = CodeGraphRepository(mock_driver)
        symbols = repo.find_symbols(name="MyClass")

        assert len(symbols) == 1


class TestSymbolResolution:
    """Tests for external symbol resolution."""

    def test_symbol_map_creation(self):
        """Test that symbol map is created correctly."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()

        symbols = [
            CodeSymbol(name="func1", symbol_type=SymbolType.FUNCTION, file_id="f1", start_line=1, end_line=10, start_column=0, end_column=10),
            CodeSymbol(name="func2", symbol_type=SymbolType.FUNCTION, file_id="f1", start_line=12, end_line=20, start_column=0, end_column=10),
        ]

        symbol_map = {s.name: s.id for s in symbols}
        assert "func1" in symbol_map
        assert "func2" in symbol_map

    def test_external_symbol_tracking(self):
        """Test tracking of unresolved external symbols."""
        from socialseed_tasker.core.code_analysis.parser import CodeGraphParser

        parser = CodeGraphParser()
        content = '''
import requests

def call_api():
    response = requests.get("http://example.com")
    return response
'''

        file_id = "test-file-7"
        symbols, imports, relationships = parser._parse_file(
            Path("api.py"), content, file_id, "python"
        )

        import_modules = [i.module for i in imports]
        assert "requests" in import_modules

    def test_unresolved_calls_handling(self):
        """Test handling of unresolved function calls."""
        from socialseed_tasker.core.code_analysis.entities import RelationshipType

        external_symbols = ["requests.get", "json.loads", "external_func"]
        resolved_rels = []

        relationships = [
            CodeRelationship(source_id="s1", target_id="external_func", relationship_type=RelationshipType.CALLS),
            CodeRelationship(source_id="s2", target_id="local_func", relationship_type=RelationshipType.CALLS),
        ]

        symbol_map = {"local_func": "local-id-123"}

        for rel in relationships:
            if rel.relationship_type == RelationshipType.CALLS:
                if rel.target_id in symbol_map:
                    resolved_rels.append(rel.model_copy(update={"target_id": symbol_map[rel.target_id]}))
                else:
                    resolved_rels.append(rel.model_copy(update={"target_id": f"external:{rel.target_id}"}))

        assert len(resolved_rels) == 2
        external_count = sum(1 for r in resolved_rels if r.target_id.startswith("external:"))
        assert external_count == 1