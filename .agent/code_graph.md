# Code-as-Graph Capability for AI Agents

## Purpose
This system allows AI agents to understand the codebase structure, dependencies, and potential impact of changes without reading every file.

## Available Tools (CLI)
Agents should use these commands via the terminal to explore the codebase:

### 1. Discovery
- `tasker code-graph stats`: Get an overview of the graph size and health.
- `tasker code-graph files --limit 20`: List files indexed in the graph.
- `tasker code-graph find [SymbolName]`: Locate the definition of a class or function.

### 2. Impact Analysis (CRITICAL)
Before modifying any code, agents MUST run:
- `tasker code-graph impact [SymbolName]`

This command returns all direct callers of the symbol. If a symbol has many callers, the change is considered **High Risk**.

### 3. Dependency Analysis
- `tasker code-graph calls <path>`: Find all callers of a function/method.
- `tasker code-graph depends <path>`: Find dependencies (imports) for a file.
- `tasker code-graph tests <path>`: Find test files for a source file.

### 4. Management
- `tasker code-graph scan <path>`: Scan repository to update the graph.
- `tasker code-graph scan <path> --incremental`: Only scan changed files.
- `tasker code-graph clear`: Clear all code graph data.

## Schema Details
- **Nodes**: `CodeFile`, `CodeSymbol`, `CodeImport`.
- **Relationships**: 
    - `DEFINES`: File -> Symbol.
    - `CONTAINS`: Class -> Method.
    - `CALLS`: Function -> Function (Behavioral dependency).
    - `IMPORTS`: File -> Module.

## API Endpoints
- `POST /api/v1/code-graph/scan`: Scan repository
- `GET /api/v1/code-graph/files`: List files
- `GET /api/v1/code-graph/symbols`: Find symbols
- `GET /api/v1/code-graph/stats`: Get statistics
- `GET /api/v1/code-graph/calls/{symbol}`: Get callers
- `GET /api/v1/code-graph/depends/{path}`: Get dependencies
- `GET /api/v1/code-graph/tests/{path}`: Get tests
- `DELETE /api/v1/code-graph`: Clear graph

## Guidelines for Agents
1. **Always Scan**: After making changes, run `tasker code-graph scan src` to update the graph.
2. **Check Callers**: If you are refactoring a function, check `impact` to ensure you update all call sites.
3. **Verify Imports**: Use `files` to see if your new file was correctly indexed.
4. **Find Tests**: Use `tests` to find related test files before making changes.
5. **Check Dependencies**: Use `depends` to see what modules a file imports.
