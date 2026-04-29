"""Code Graph Repository - Neo4j storage for code-as-graph feature.

Provides storage and retrieval of parsed code structure including files,
symbols, imports, and relationships.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from socialseed_tasker.core.code_analysis.entities import (
    CodeFile,
    CodeGraphStats,
    CodeImport,
    CodeRelationship,
    CodeSymbol,
    RelationshipType,
    SymbolType,
)

CODE_GRAPH_QUERIES = {
    "create_file": """
        MERGE (f:CodeFile {id: $id})
        SET f.path = $path,
            f.language = $language,
            f.lines_of_code = $lines_of_code,
            f.file_hash = $file_hash,
            f.commit_sha = $commit_sha,
            f.scanned_at = $scanned_at,
            f.repository_path = $repository_path
        RETURN f
    """,
    "create_symbol": """
        MERGE (s:CodeSymbol {id: $id})
        SET s.name = $name,
            s.symbol_type = $symbol_type,
            s.file_id = $file_id,
            s.start_line = $start_line,
            s.end_line = $end_line,
            s.start_column = $start_column,
            s.end_column = $end_column,
            s.parameters = $parameters,
            s.return_type = $return_type,
            s.decorators = $decorators,
            s.is_test = $is_test,
            s.parent_symbol_id = $parent_symbol_id
        RETURN s
    """,
    "create_import": """
        MERGE (i:CodeImport {id: $id})
        SET i.file_id = $file_id,
            i.module = $module,
            i.names = $names,
            i.alias = $alias,
            i.line_number = $line_number,
            i.is_from = $is_from
        RETURN i
    """,
    "create_relationship": """
        MATCH (s {id: $source_id})
        MATCH (t {id: $target_id})
        MERGE (s)-[r:CODE_RELATIONSHIP {id: $id}]->(t)
        SET r.relationship_type = $relationship_type,
            r.created_at = $created_at,
            r.commit_sha = $commit_sha
        RETURN r
    """,
    "link_file_to_symbol": """
        MATCH (f:CodeFile {id: $file_id})
        MATCH (s:CodeSymbol {id: $symbol_id})
        MERGE (f)-[:CONTAINS]->(s)
    """,
    "link_file_to_import": """
        MATCH (f:CodeFile {id: $file_id})
        MATCH (i:CodeImport {id: $import_id})
        MERGE (f)-[:IMPORTS]->(i)
    """,
    "get_files": """
        MATCH (f:CodeFile)
        RETURN f
        ORDER BY f.path
        LIMIT $limit
    """,
    "get_file_by_path": """
        MATCH (f:CodeFile {path: $path, repository_path: $repo_path})
        RETURN f
    """,
    "get_symbols_by_name": """
        MATCH (s:CodeSymbol)
        WHERE s.name CONTAINS $name
        RETURN s
        LIMIT $limit
    """,
    "get_symbols_by_type": """
        MATCH (s:CodeSymbol {symbol_type: $symbol_type})
        RETURN s
        LIMIT $limit
    """,
    "get_symbols_by_file": """
        MATCH (f:CodeFile {id: $file_id})-[:CONTAINS]->(s:CodeSymbol)
        RETURN s
    """,
    "get_imports_by_file": """
        MATCH (f:CodeFile {id: $file_id})-[:IMPORTS]->(i:CodeImport)
        RETURN i
    """,
    "get_relationships": """
        MATCH (s)-[r:CODE_RELATIONSHIP]->(t)
        RETURN s.id AS source_id, t.id AS target_id, r.relationship_type, r.created_at
        LIMIT $limit
    """,
    "get_callers": """
        MATCH (s:CodeSymbol {name: $name})-[r:CODE_RELATIONSHIP {relationship_type: 'calls'}]->(t:CodeSymbol)
        RETURN t
    """,
    "get_dependencies": """
        MATCH (f:CodeFile {path: $path, repository_path: $repo_path})-[:IMPORTS]->(i:CodeImport)
        RETURN i.module AS module
    """,
    "get_stats": """
        MATCH (f:CodeFile)
        OPTIONAL MATCH (f)-[:CONTAINS]->(s:CodeSymbol)
        OPTIONAL MATCH ()-[r:CODE_RELATIONSHIP]->()
        RETURN count(DISTINCT f) AS total_files,
               count(DISTINCT s) AS total_symbols,
               count(DISTINCT r) AS total_relationships,
               collect(DISTINCT f.language) AS languages
    """,
    "clear_graph": """
        MATCH (n)
        WHERE n:CodeFile OR n:CodeSymbol OR n:CodeImport
        DETACH DELETE n
    """,
    "create_indexes": """
        CREATE INDEX code_file_path IF NOT EXISTS FOR (f:CodeFile) ON (f.path)
        CREATE INDEX code_file_repo IF NOT EXISTS FOR (f:CodeFile) ON (f.repository_path)
        CREATE INDEX code_symbol_name IF NOT EXISTS FOR (s:CodeSymbol) ON (s.name)
        CREATE INDEX code_symbol_type IF NOT EXISTS FOR (s:CodeSymbol) ON (s.symbol_type)
        CREATE INDEX code_symbol_file IF NOT EXISTS FOR (s:CodeSymbol) ON (s.file_id)
        CREATE INDEX code_import_file IF NOT EXISTS FOR (i:CodeImport) ON (i.file_id)
    """,
}


class CodeGraphRepository:
    """Repository for storing and retrieving code graph data in Neo4j."""

    def __init__(self, driver: Any):
        self._driver = driver

    def save_scan_results(
        self,
        files: list[CodeFile],
        symbols: list[CodeSymbol],
        imports: list[CodeImport],
        relationships: list[CodeRelationship],
    ) -> None:
        """Save scan results to Neo4j.

        Args:
            files: List of code files to save
            symbols: List of code symbols to save
            imports: List of imports to save
            relationships: List of relationships to save
        """
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                for file in files:
                    tx.run(
                        CODE_GRAPH_QUERIES["create_file"],
                        id=str(file.id),
                        path=file.path,
                        language=file.language,
                        lines_of_code=file.lines_of_code,
                        file_hash=file.file_hash,
                        commit_sha=file.commit_sha,
                        scanned_at=file.scanned_at.isoformat(),
                        repository_path=file.repository_path,
                    )

                for symbol in symbols:
                    tx.run(
                        CODE_GRAPH_QUERIES["create_symbol"],
                        id=str(symbol.id),
                        name=symbol.name,
                        symbol_type=symbol.symbol_type.value,
                        file_id=str(symbol.file_id),
                        start_line=symbol.start_line,
                        end_line=symbol.end_line,
                        start_column=symbol.start_column,
                        end_column=symbol.end_column,
                        parameters=symbol.parameters,
                        return_type=symbol.return_type,
                        decorators=symbol.decorators,
                        is_test=symbol.is_test,
                        parent_symbol_id=str(symbol.parent_symbol_id) if symbol.parent_symbol_id else None,
                    )

                    tx.run(
                        CODE_GRAPH_QUERIES["link_file_to_symbol"],
                        file_id=str(symbol.file_id),
                        symbol_id=str(symbol.id),
                    )

                for imp in imports:
                    tx.run(
                        CODE_GRAPH_QUERIES["create_import"],
                        id=str(imp.id),
                        file_id=str(imp.file_id),
                        module=imp.module,
                        names=imp.names,
                        alias=imp.alias,
                        line_number=imp.line_number,
                        is_from=imp.is_from,
                    )

                    tx.run(
                        CODE_GRAPH_QUERIES["link_file_to_import"],
                        file_id=str(imp.file_id),
                        import_id=str(imp.id),
                    )

                for rel in relationships:
                    tx.run(
                        CODE_GRAPH_QUERIES["create_relationship"],
                        id=str(rel.id),
                        source_id=str(rel.source_id),
                        target_id=str(rel.target_id),
                        relationship_type=rel.relationship_type.value,
                        created_at=rel.created_at.isoformat(),
                        commit_sha=rel.commit_sha,
                    )

                tx.commit()

    def get_files(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get code files from the graph."""
        with self._driver.session() as session:
            result = session.run(CODE_GRAPH_QUERIES["get_files"], limit=limit)
            return [dict(record["f"]) for record in result]

    def get_file_by_path(self, path: str, repo_path: str) -> dict[str, Any] | None:
        """Get a file by its path."""
        with self._driver.session() as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_file_by_path"],
                path=path,
                repo_path=repo_path,
            )
            record = result.single()
            return dict(record["f"]) if record else None

    def find_symbols(self, name: str | None = None, symbol_type: SymbolType | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Find symbols by name or type."""
        with self._driver.session() as session:
            if name:
                result = session.run(
                    CODE_GRAPH_QUERIES["get_symbols_by_name"],
                    name=name,
                    limit=limit,
                )
            elif symbol_type:
                result = session.run(
                    CODE_GRAPH_QUERIES["get_symbols_by_type"],
                    symbol_type=symbol_type.value,
                    limit=limit,
                )
            else:
                return []

            return [dict(record["s"]) for record in result]

    def get_symbols_by_file(self, file_id: UUID) -> list[dict[str, Any]]:
        """Get all symbols for a file."""
        with self._driver.session() as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_symbols_by_file"],
                file_id=str(file_id),
            )
            return [dict(record["s"]) for record in result]

    def get_imports_by_file(self, file_id: UUID) -> list[dict[str, Any]]:
        """Get all imports for a file."""
        with self._driver.session() as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_imports_by_file"],
                file_id=str(file_id),
            )
            return [dict(record["i"]) for record in result]

    def get_dependencies(self, path: str, repo_path: str) -> list[str]:
        """Get dependencies for a file."""
        with self._driver.session() as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_dependencies"],
                path=path,
                repo_path=repo_path,
            )
            return [record["module"] for record in result]

    def get_callers(self, symbol_name: str) -> list[dict[str, Any]]:
        """Get symbols that call the given symbol."""
        with self._driver.session() as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_callers"],
                name=symbol_name,
            )
            return [dict(record["t"]) for record in result]

    def get_stats(self) -> CodeGraphStats:
        """Get code graph statistics."""
        with self._driver.session() as session:
            result = session.run(CODE_GRAPH_QUERIES["get_stats"])
            record = result.single()
            if record:
                return CodeGraphStats(
                    total_files=record["total_files"],
                    total_symbols=record["total_symbols"],
                    total_relationships=record["total_relationships"],
                )
            return CodeGraphStats()

    def clear(self) -> None:
        """Clear all code graph data."""
        with self._driver.session() as session:
            session.run(CODE_GRAPH_QUERIES["clear_graph"])

    def create_indexes(self) -> None:
        """Create indexes for code graph."""
        with self._driver.session() as session:
            session.run(CODE_GRAPH_QUERIES["create_indexes"])