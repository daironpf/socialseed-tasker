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

## Schema Details
- **Nodes**: `CodeFile`, `CodeSymbol`, `CodeImport`.
- **Relationships**: 
    - `DEFINES`: File -> Symbol.
    - `CONTAINS`: Class -> Method.
    - `CALLS`: Function -> Function (Behavioral dependency).
    - `IMPORTS`: File -> Module.

## Guidelines for Agents
1. **Always Scan**: After making changes, run `tasker code-graph scan src` to update the graph.
2. **Check Callers**: If you are refactoring a function, check `impact` to ensure you update all call sites.
3. **Verify Imports**: Use `files` to see if your new file was correctly indexed.
