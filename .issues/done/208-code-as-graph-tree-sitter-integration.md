# Issue #208: Code-as-Graph with Tree-sitter Integration

## Description

Implement Tree-sitter parser integration to map the entire repository as a graph structure in Neo4j, enabling deep code understanding for AI agents.

## Problem

AI agents need to understand code structure beyond just tasks and dependencies. They need to know:
- How functions call each other
- What classes exist in a file
- What tests cover what code
- What dependencies exist between modules

## Expected Behavior

The system parses source code repositories and stores the graph structure in Neo4j with:

### Node Types
- `File` - Source files with path, language, lines of code
- `Class` - Classes with methods and attributes
- `Function` - Functions with parameters and return types
- `Import` - Import statements and their targets
- `Test` - Test files linked to tested units

### Relationship Types
- `[:CALLS]` - Function/Method invocations
- `[:DEPENDS_ON]` - Import/Dependency relationships
- `[:DEFINES]` - File defines Class/Function
- `[:TESTS]` - Test file tests Class/Function
- `[:CONTAINS]` - File contains Function/Class
- `[:CODE_RELATIONSHIP]` - General code relationships

## Technical Implementation

### Tree-sitter Integration
- Use `tree-sitter` Python bindings for parsing
- Support multiple languages: Python, JavaScript, TypeScript, Go, Rust, Java, C++
- Parse file contents and extract AST (Abstract Syntax Tree)
- Convert AST nodes to graph nodes
- Convert AST relationships to graph relationships

### Incremental Scanning
- Track file modification via git diff
- Only re-parse changed files
- Store last scan timestamp in Neo4j

### Symbol Resolution
- External symbols marked with prefixes: `external:`, `imported:`, `unresolved:`
- Resolution based on import statements

### Storage
- `CodeGraphRepository` in `storage/graph_database/`
- Use `session.run()` with dict parameters for Neo4j driver v6

## Status

**COMPLETED** ✅

## Priority

**HIGH** - Core feature for v0.9.0

## Component

CORE, STORAGE

## Acceptance Criteria

- [x] Tree-sitter parser integration for Python, JS, TS, Go, Rust, Java, C++
- [x] Node types: File, Class, Function, Import, Test, Method, Variable
- [x] Relationship types: CALLS, DEPENDS_ON, DEFINES, TESTS, CONTAINS, IMPORTS
- [x] Incremental scanning (only changed files with git diff)
- [x] Git-aware (file history tracking via commit SHA)
- [x] Symbol index for fast lookups
- [x] CLI command: `tasker code-graph scan <path>`
- [x] CLI command: `tasker code-graph scan <path> --incremental`
- [x] CLI command: `tasker code-graph find <symbol>`
- [x] CLI command: `tasker code-graph files`
- [x] CLI command: `tasker code-graph stats`
- [x] CLI command: `tasker code-graph clear`
- [x] API endpoint: `POST /api/v1/code-graph/scan`
- [x] API endpoint: `GET /api/v1/code-graph/files`
- [x] API endpoint: `GET /api/v1/code-graph/symbols`
- [x] API endpoint: `GET /api/v1/code-graph/stats`
- [x] API endpoint: `DELETE /api/v1/code-graph`
- [x] Unit tests for parser integration (25 tests)

## Implementation Details

### Files Created/Modified

| File | Purpose |
|------|---------|
| `src/.../core/code_analysis/entities.py` | CodeGraph entities: CodeFile, CodeSymbol, CodeImport, CodeRelationship |
| `src/.../core/code_analysis/parser.py` | CodeGraphParser with tree-sitter integration |
| `src/.../core/code_analysis/__init__.py` | Module exports |
| `src/.../storage/graph_database/code_graph_repository.py` | Neo4j storage for code graph |
| `src/.../entrypoints/terminal_cli/commands.py` | CLI commands |
| `src/.../entrypoints/web_api/routes.py` | API endpoints |
| `src/.../entrypoints/web_api/__main__.py` | Fixed driver initialization |
| `src/.../entrypoints/web_api/app.py` | Added driver to app.state |
| `tests/unit/test_code_graph.py` | 25 unit tests |

### API Integration Fixes

During testing, the following bugs were fixed:
1. Driver not passed to `create_app()` in `__main__.py`
2. Driver not available in `app.state.driver`
3. `get_code_graph_driver()` dependency needed in endpoints
4. `session.run()` instead of `tx.run()` for Neo4j driver v6
5. Parameters passed as dict instead of kwargs

## Usage

### CLI
```bash
tasker code-graph scan /path/to/repo
tasker code-graph scan /path/to/repo --incremental
tasker code-graph find MyClass
tasker code-graph files
tasker code-graph stats
tasker code-graph clear
```

### API
```bash
curl -X POST "http://localhost:8000/api/v1/code-graph/scan?path=src&incremental=false"
curl -s "http://localhost:8000/api/v1/code-graph/stats"
```

## Impact

- Enables AI agents to understand code structure
- Supports "find usages" and "go to definition"
- Enables code dependency analysis
- Supports test coverage mapping

## Related Issues

- #209 - RAG Native with Vector Indexes
- #210 - AI Reasoning Logs in Graph
- #211 - Code Graph CLI and API Commands
- #214 - Neo4j Schema Migration for v0.9.0
- #215 - Agent Integration with Code-as-Graph and RAG

## Technical Notes

- Tree-sitter requires C++ build tools (included in Docker)
- Large repositories handled efficiently via incremental scanning
- External symbol resolution improves query accuracy
- Neo4j driver v6 requires dict parameters for queries

## Test Results

```
=== Scan (small path) ===
{"files":5,"symbols":140,"imports":23,"relationships":272,"saved_to_graph":true}

=== Stats ===
{"total_files":230,"total_symbols":5711,"total_relationships":4786}
```

All 25 unit tests passing ✅