"""Code Graph Repository - Neo4j storage for code-as-graph feature.

Provides storage and retrieval of parsed code structure including files,
symbols, imports, and relationships.
"""

from __future__ import annotations

from datetime import datetime, timezone
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
from socialseed_tasker.storage.graph_database import queries


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


CODE_GRAPH_QUERIES = {
    "create_file": """
        MERGE (f:CodeFile {id: $id})
        SET f.name = $name,
            f.path = $path,
            f.language = $language,
            f.linesOfCode = $linesOfCode,
            f.fileHash = $fileHash,
            f.commitSha = $commitSha,
            f.scannedAt = $scannedAt,
            f.repositoryPath = $repositoryPath
        RETURN f
    """,
    "create_symbol": """
        MERGE (s:CodeSymbol {id: $id})
        SET s.name = $name,
            s.symbolType = $symbolType,
            s.fileId = $fileId,
            s.startLine = $startLine,
            s.endLine = $endLine,
            s.startColumn = $startColumn,
            s.endColumn = $endColumn,
            s.parameters = $parameters,
            s.returnType = $returnType,
            s.decorators = $decorators,
            s.isTest = $isTest,
            s.parentSymbolId = $parentSymbolId
        RETURN s
    """,
    "create_import": """
        MERGE (i:CodeImport {id: $id})
        SET i.fileId = $fileId,
            i.module = $module,
            i.names = $names,
            i.alias = $alias,
            i.lineNumber = $lineNumber,
            i.isFrom = $isFrom
        RETURN i
    """,
    "create_relationship": """
        MATCH (s {id: $sourceId})
        MATCH (t {id: $targetId})
        MERGE (s)-[r:CODE_RELATIONSHIP {id: $id}]->(t)
        SET r.relationshipType = $relationshipType,
            r.createdAt = $createdAt,
            r.commitSha = $commitSha
        RETURN r
    """,
    "link_file_to_symbol": """
        MATCH (f:CodeFile {id: $fileId})
        MATCH (s:CodeSymbol {id: $symbolId})
        MERGE (f)-[:CONTAINS]->(s)
    """,
    "link_file_to_import": """
        MATCH (f:CodeFile {id: $fileId})
        MATCH (i:CodeImport {id: $importId})
        MERGE (f)-[:IMPORTS]->(i)
    """,
    "get_files": """
        MATCH (f:CodeFile)
        RETURN f
        ORDER BY f.path
        LIMIT $limit
    """,
    "get_file_by_path": """
        MATCH (f:CodeFile {path: $path, repositoryPath: $repoPath})
        RETURN f
    """,
    "get_symbols_by_name": """
        MATCH (s:CodeSymbol)
        WHERE s.name CONTAINS $name
        RETURN s
        LIMIT $limit
    """,
    "get_symbols_by_type": """
        MATCH (s:CodeSymbol {symbolType: $symbolType})
        RETURN s
        LIMIT $limit
    """,
    "get_symbols_by_file": """
        MATCH (f:CodeFile {id: $fileId})-[:CONTAINS]->(s:CodeSymbol)
        RETURN s
    """,
    "get_imports_by_file": """
        MATCH (f:CodeFile {id: $fileId})-[:IMPORTS]->(i:CodeImport)
        RETURN i
    """,
    "get_relationships": """
        MATCH (s)-[r:CODE_RELATIONSHIP]->(t)
        RETURN s.id AS sourceId, t.id AS targetId, r.relationshipType, r.createdAt
        LIMIT $limit
    """,
    "get_callers": """
        MATCH (s:CodeSymbol {name: $name})-[r:CODE_RELATIONSHIP {relationshipType: 'calls'}]->(t:CodeSymbol)
        RETURN t
    """,
    "get_dependencies": """
        MATCH (f:CodeFile {path: $path, repositoryPath: $repoPath})-[:IMPORTS]->(i:CodeImport)
        RETURN i.module AS module
    """,
    "get_stats": """
        MATCH (f:CodeFile)
        OPTIONAL MATCH (f)-[:CONTAINS]->(s:CodeSymbol)
        OPTIONAL MATCH ()-[r:CODE_RELATIONSHIP]->()
        RETURN count(DISTINCT f) AS totalFiles,
               count(DISTINCT s) AS totalSymbols,
               count(DISTINCT r) AS totalRelationships,
               collect(DISTINCT f.language) AS languages
    """,
    "clear_graph": """
        MATCH (n)
        WHERE n:CodeFile OR n:CodeSymbol OR n:CodeImport
        DETACH DELETE n
    """,
    "create_indexes": """
        CREATE INDEX code_filePath IF NOT EXISTS FOR (f:CodeFile) ON (f.path)
        CREATE INDEX code_file_repo IF NOT EXISTS FOR (f:CodeFile) ON (f.repositoryPath)
        CREATE INDEX code_symbol_name IF NOT EXISTS FOR (s:CodeSymbol) ON (s.name)
        CREATE INDEX code_symbolType IF NOT EXISTS FOR (s:CodeSymbol) ON (s.symbolType)
        CREATE INDEX code_symbol_file IF NOT EXISTS FOR (s:CodeSymbol) ON (s.fileId)
        CREATE INDEX code_import_file IF NOT EXISTS FOR (i:CodeImport) ON (i.fileId)
    """,
    # Impact Analysis queries (direct :CALLS relationship)
    "get_direct_callers": """
        MATCH (caller:CodeSymbol)-[:CALLS]->(s:CodeSymbol {id: $symbolId})
        RETURN caller.id as id, caller.name as name, caller.symbolType as symbolType
    """,
    "get_transitive_callers": """
        MATCH (caller:CodeSymbol)-[:CALLS*1..3]->(s:CodeSymbol {id: $symbolId})
        RETURN DISTINCT caller.id as id, caller.name as name, caller.symbolType as symbolType,
               length((caller)-[:CALLS*1..3]->(s)) as depth
        ORDER BY depth
    """,
    "get_direct_callees": """
        MATCH (s:CodeSymbol {id: $symbolId})-[:CALLS]->(callee:CodeSymbol)
        RETURN callee.id as id, callee.name as name, callee.symbolType as symbolType
    """,
    "get_symbol_by_id": """
        MATCH (s:CodeSymbol {id: $symbolId})
        RETURN s.id as id, s.name as name, s.symbolType as symbolType,
               s.startLine as startLine, s.endLine as endLine, s.fileId as fileId
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
        with self._driver.driver.session(database=self._driver.database) as session:
            for file in files:
                session.run(
                    CODE_GRAPH_QUERIES["create_file"],
                    {"id": str(file.id), "name": file.name, "path": file.path, "language": file.language,
                     "linesOfCode": file.linesOfCode, "fileHash": file.fileHash,
                     "commitSha": file.commitSha, "scannedAt": file.scannedAt.isoformat(),
                     "repositoryPath": file.repositoryPath}
                )

            for symbol in symbols:
                session.run(
                    CODE_GRAPH_QUERIES["create_symbol"],
                    {"id": str(symbol.id), "name": symbol.name, "symbolType": symbol.symbolType.value,
                     "fileId": str(symbol.fileId), "startLine": symbol.startLine, "endLine": symbol.endLine,
                     "startColumn": symbol.startColumn, "endColumn": symbol.endColumn,
                     "parameters": symbol.parameters, "returnType": symbol.returnType,
                     "decorators": symbol.decorators, "isTest": symbol.isTest,
                     "parentSymbolId": str(symbol.parentSymbolId) if symbol.parentSymbolId else None}
                )

                session.run(
                    CODE_GRAPH_QUERIES["link_file_to_symbol"],
                    {"fileId": str(symbol.fileId), "symbolId": str(symbol.id)}
                )

            for imp in imports:
                session.run(
                    CODE_GRAPH_QUERIES["create_import"],
                    {"id": str(imp.id), "fileId": str(imp.fileId), "module": imp.module,
                     "names": imp.names, "alias": imp.alias, "lineNumber": imp.lineNumber,
                     "isFrom": imp.isFrom}
                )

                session.run(
                    CODE_GRAPH_QUERIES["link_file_to_import"],
                    {"fileId": str(imp.fileId), "importId": str(imp.id)}
                )

            for rel in relationships:
                session.run(
                    CODE_GRAPH_QUERIES["create_relationship"],
                    {"id": str(rel.id), "sourceId": str(rel.sourceId), "targetId": str(rel.targetId),
                     "relationshipType": rel.relationshipType.value,
                     "createdAt": rel.createdAt.isoformat(), "commitSha": rel.commitSha}
                )

    def get_files(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get code files from the graph."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(CODE_GRAPH_QUERIES["get_files"], limit=limit)
            return [dict(record["f"]) for record in result]

    def get_file_by_path(self, path: str, repoPath: str) -> dict[str, Any] | None:
        """Get a file by its path."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_file_by_path"],
                path=path,
                repoPath=repoPath,
            )
            record = result.single()
            return dict(record["f"]) if record else None

    def find_symbols(self, name: str | None = None, symbolType: SymbolType | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Find symbols by name or type."""
        with self._driver.driver.session(database=self._driver.database) as session:
            if name:
                result = session.run(
                    CODE_GRAPH_QUERIES["get_symbols_by_name"],
                    name=name,
                    limit=limit,
                )
            elif symbolType:
                result = session.run(
                    CODE_GRAPH_QUERIES["get_symbols_by_type"],
                    symbolType=symbolType.value,
                    limit=limit,
                )
            else:
                return []

            results = []
            for record in result:
                data = dict(record["s"])
                data["filePath"] = record.get("filePath")
                results.append(data)
            return results

    def get_symbols_by_file(self, fileId: UUID) -> list[dict[str, Any]]:
        """Get all symbols for a file."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_symbols_by_file"],
                fileId=str(fileId),
            )
            results = []
            for record in result:
                data = dict(record["s"])
                data["filePath"] = record.get("filePath")
                results.append(data)
            return results

    def get_imports_by_file(self, fileId: UUID) -> list[dict[str, Any]]:
        """Get all imports for a file."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_imports_by_file"],
                fileId=str(fileId),
            )
            return [dict(record["i"]) for record in result]

    def get_dependencies(self, path: str, repoPath: str) -> list[str]:
        """Get dependencies for a file."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_dependencies"],
                path=path,
                repoPath=repoPath,
            )
            return [record["module"] for record in result]

    def get_callers(self, symbol_name: str) -> list[dict[str, Any]]:
        """Get symbols that call the given symbol."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_callers"],
                name=symbol_name,
            )
            return [dict(record["t"]) for record in result]

    # -- Impact Analysis (CALLS relationship) --------------------------------

    def get_direct_callers(self, symbol_id: str) -> list[dict[str, Any]]:
        """Get symbols that directly call this symbol (who depends on it)."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_direct_callers"],
                symbolId=symbol_id,
            )
            return [
                {"id": r["id"], "name": r["name"], "symbol_type": r["symbolType"]}
                for r in result
            ]

    def get_transitive_callers(self, symbol_id: str, depth: int = 3) -> list[dict[str, Any]]:
        """Get all symbols that call this symbol (transitive closure)."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                """
                MATCH (caller:CodeSymbol)-[:CALLS*1..$depth]->(s:CodeSymbol {id: $symbolId})
                RETURN DISTINCT caller.id as id, caller.name as name, caller.symbolType as symbolType,
                       length((caller)-[:CALLS*1..]->(s)) as depth
                ORDER BY depth
                """,
                symbolId=symbol_id,
                depth=depth,
            )
            return [
                {"id": r["id"], "name": r["name"], "symbol_type": r["symbolType"], "depth": r["depth"]}
                for r in result
            ]

    def get_direct_callees(self, symbol_id: str) -> list[dict[str, Any]]:
        """Get symbols that this symbol directly calls (what it depends on)."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_direct_callees"],
                symbolId=symbol_id,
            )
            return [
                {"id": r["id"], "name": r["name"], "symbol_type": r["symbolType"]}
                for r in result
            ]

    def get_symbol_by_id(self, symbol_id: str) -> dict[str, Any] | None:
        """Get a CodeSymbol by its ID."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                CODE_GRAPH_QUERIES["get_symbol_by_id"],
                symbolId=symbol_id,
            )
            record = result.single()
            if record:
                return {
                    "id": record["id"],
                    "name": record["name"],
                    "symbol_type": record["symbolType"],
                    "start_line": record.get("startLine"),
                    "end_line": record.get("endLine"),
                    "file_id": record.get("fileId"),
                }
            return None

    def analyze_impact(self, symbol_id: str, include_transitive: bool = True) -> dict[str, Any]:
        """Full impact analysis for a CodeSymbol."""
        direct_callers = self.get_direct_callers(symbol_id)
        callees = self.get_direct_callees(symbol_id)
        
        result = {
            "symbol": self.get_symbol_by_id(symbol_id),
            "direct_callers_count": len(direct_callers),
            "direct_callers": direct_callers,
            "direct_callees_count": len(callees),
            "direct_callees": callees,
        }
        
        if include_transitive:
            transitive = self.get_transitive_callers(symbol_id)
            result["transitive_callers_count"] = len(transitive)
            result["transitive_callers"] = transitive
            result["risk_level"] = self._calculate_risk_level(len(direct_callers), len(transitive))
        
        return result

    def _calculate_risk_level(self, direct: int, transitive: int) -> str:
        """Calculate risk level based on impact scope."""
        total = direct + transitive
        if total == 0:
            return "NONE"
        elif total <= 5:
            return "LOW"
        elif total <= 20:
            return "MEDIUM"
        else:
            return "HIGH"

    def get_stats(self) -> CodeGraphStats:
        """Get code graph statistics."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(CODE_GRAPH_QUERIES["get_stats"])
            record = result.single()
            if record:
                return CodeGraphStats(
                    totalFiles=record["totalFiles"],
                    totalSymbols=record["totalSymbols"],
                    totalRelationships=record["totalRelationships"],
                )
            return CodeGraphStats()

    def clear(self) -> None:
        """Clear all code graph data."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(CODE_GRAPH_QUERIES["clear_graph"])

    def create_indexes(self) -> None:
        """Create indexes for code graph."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(CODE_GRAPH_QUERIES["create_indexes"])

    def get_callers_by_path(self, path: str) -> list[dict[str, Any]]:
        """Get all functions that call symbols in a file."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                """
                MATCH (f:CodeFile {path: $path})<-[:DEFINES]-(s:CodeSymbol)
                MATCH (c:CodeSymbol)-[:CALLS]->(s)
                MATCH (cf:CodeFile)<-[:DEFINES]-(c)
                RETURN c.name as name, c.symbolType as symbolType, cf.path as filePath
                """,
                {"path": path},
            )
            return [
                {
                    "name": r["name"],
                    "symbolType": r["symbolType"],
                    "filePath": r["filePath"],
                }
                for r in result
            ]

    def get_dependencies_by_path(self, path: str) -> list[dict[str, Any]]:
        """Get imports/dependencies for a file."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                """
                MATCH (f:CodeFile {path: $path})
                MATCH (f)<-[:IMPORTS]-(i:CodeImport)
                RETURN i.module as module, i.lineNumber as lineNumber, i.isFrom as isFrom
                """,
                {"path": path},
            )
            return [
                {
                    "module": r["module"],
                    "lineNumber": r["lineNumber"],
                    "isFrom": r["isFrom"],
                }
                for r in result
            ]

    def get_tests_for_file(self, path: str) -> list[dict[str, Any]]:
        """Get test files related to a source file."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                """
                MATCH (f:CodeFile {path: $path})
                MATCH (tf:CodeFile)<-[:DEFINES]-(ts:CodeSymbol {isTest: true})
                WHERE tf.path CONTAINS 'test' OR tf.path CONTAINS 'spec'
                RETURN tf.path as path, ts.symbolType as symbolType
                """,
                {"path": path},
            )
            return [
                {"path": r["path"], "symbolType": r["symbolType"]}
                for r in result
            ]

    def link_issue_to_file(self, issueId: str, filePath: str) -> dict[str, Any]:
        """Link an issue to a code file (when closing the issue)."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.ISSUE_AFFECTS_FILE,
                {"issueId": issueId, "filePath": filePath, "closedAt": _now_iso()},
            )
            record = result.single()
            if record is None:
                return {"success": False, "error": "Issue or file not found"}
            return {"success": True, "issueId": issueId, "filePath": filePath}

    def get_issues_affecting_file(self, filePath: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get all issues that affected a file."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.FIND_ISSUES_AFFECTING_FILE,
                {"filePath": filePath, "limit": limit},
            )
            return [
                {
                    "issueId": r["issueId"],
                    "title": r["title"],
                    "closedAt": r["closedAt"],
                }
                for r in result
            ]

    def link_issue_to_symbol(self, issueId: str, symbolId: str) -> dict[str, Any]:
        """Link an issue to a code symbol."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.ISSUE_AFFECTS_SYMBOL,
                {"issueId": issueId, "symbolId": symbolId, "closedAt": _now_iso()},
            )
            record = result.single()
            if record is None:
                return {"success": False, "error": "Issue or symbol not found"}
            return {"success": True, "issueId": issueId, "symbolId": symbolId}

    def get_issues_affecting_symbol(self, symbol_name: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get all issues that affected a symbol."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                queries.FIND_ISSUES_AFFECTING_SYMBOL,
                {"symbol_name": symbol_name, "limit": limit},
            )
            return [
                {
                    "issueId": r["issueId"],
                    "title": r["title"],
                    "symbol_name": r["symbol_name"],
                    "closedAt": r["closedAt"],
                }
                for r in result
            ]