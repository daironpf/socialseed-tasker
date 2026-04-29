# Issue #208: Code-as-Graph with Tree-sitter Integration

## Description

Implement Tree-sitter parser integration to map the entire repository as a graph structure, enabling deep code understanding for AI agents.

## Problem

AI agents need to understand code structure beyond just tasks and dependencies. They need to know:
- How functions call each other
- What classes exist in a file
- What tests cover what code
- What dependencies exist between modules

## Expected Behavior

The system should parse source code repositories and store the graph structure in Neo4j with:
- **Node Types:**
  - `File` - Source files with path, language, lines of code
  - `Class` - Classes with methods and attributes
  - `Function` - Functions with parameters and return types
  - `Import` - Import statements and their targets
  - `Test` - Test files linked to tested units

- **Relationship Types:**
  - `[:CALLS]` - Function/Method invocations
  - `[:DEPENDS_ON]` - Import/Dependency relationships
  - `[:DEFINES]` - File defines Class/Function
  - `[:TESTS]` - Test file tests Class/Function
  - `[:CONTAINS]` - File contains Function/Class

## Technical Implementation

### Tree-sitter Integration
- Use `tree-sitter` Python bindings for parsing
- Support multiple languages: Python, JavaScript, TypeScript, Go, Rust, Java
- Parse file contents and extract AST (Abstract Syntax Tree)
- Convert AST nodes to graph nodes
- Convert AST relationships to graph relationships

### Incremental Scanning
- Track file modification times
- Only re-parse changed files (git diff based)
- Store last scan timestamp in Neo4j
- Avoid full repository rescans

### Git-Aware Parsing
- Track file history via Git
- Link nodes to commit SHAs
- Support "code at commit" queries
- Store file rename history

### Symbol Index
- Create index on node properties for fast lookups
- Support symbol search by name
- Support "find usages" queries
- Support "go to definition" queries

## Steps to Reproduce

```bash
# Not currently implemented - this is the feature to add
tasker code-graph scan /path/to/repo
# Should parse and store in Neo4j
```

## Status

**COMPLETED** ✅

## Priority

**HIGH** - Core feature for v0.9.0

## Component

CORE, STORAGE

## Acceptance Criteria

- [x] Tree-sitter parser integration for Python, JS, TS, Go, Rust
- [x] Node types: File, Class, Function, Import, Test
- [x] Relationship types: CALLS, DEPENDS_ON, DEFINES, TESTS, CONTAINS
- [x] Incremental scanning (only changed files)
- [x] Git-aware (file history tracking)
- [x] Symbol index for fast lookups
- [x] CLI command: `tasker code-graph scan <path>`
- [x] CLI command: `tasker code-graph find <symbol>`
- [x] CLI command: `tasker code-graph files`
- [x] CLI command: `tasker code-graph stats`
- [x] CLI command: `tasker code-graph clear`
- [x] API endpoint: `POST /api/v1/code-graph/scan`
- [x] API endpoint: `GET /api/v1/code-graph/files`
- [x] API endpoint: `GET /api/v1/code-graph/symbols`
- [x] API endpoint: `GET /api/v1/code-graph/stats`
- [x] API endpoint: `DELETE /api/v1/code-graph`
- [x] Unit tests for parser integration

## Implementation Plan

### Phase 1: Core Parser
1. Create `tree_sitter_parser.py` in `core/code_analysis/`
2. Implement language detection
3. Implement basic AST extraction
4. Create node extraction for each language

### Phase 2: Graph Storage
1. Create CodeGraphRepository in `storage/graph_database/`
2. Define node creation queries
3. Define relationship creation queries
4. Implement incremental update logic

### Phase 3: CLI/API Integration
1. Add commands to CLI
2. Add endpoints to API
3. Add progress tracking
4. Add error handling

## Impact

- Enables AI agents to understand code structure
- Supports "find usages" and "go to definition"
- Enables code dependency analysis
- Supports test coverage mapping

## Related Issues

- #209 - RAG Native with Vector Indexes
- #210 - AI Reasoning Logs in Graph

## Technical Notes

- Tree-sitter requires C++ build tools
- Need to handle large repositories efficiently
- Consider async parsing for better performance
- Store parsing results in Neo4j for query speed