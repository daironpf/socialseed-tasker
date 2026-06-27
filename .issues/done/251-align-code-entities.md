# Issue #251: Align Code-as-Graph Pillar Entities (File, Symbol, Import)

## Description

The "Code-as-Graph" pillar allows the system to treat source code as a queryable graph. This issue focuses on aligning the granular AST entities in `src/socialseed_tasker/core/code_analysis/entities.py`.

### Required Changes

#### 1. `CodeFile` (n6)
- Properties: `id`, `name`, `path`, `language`, `linesOfCode`, `fileHash`, `repositoryPath`, `commitSha`, `scannedAt`.
- **Relationship**: `(Component)-[:CONTAINS]->(CodeFile)`.

#### 2. `CodeSymbol` (n7)
- Properties: `id`, `name`, `symbolType`, `startLine`, `endLine`, `startColumn`, `endColumn`, `parameters`, `returnType`, `decorators`, `isTest`.
- **Relationship**: `(CodeFile)-[:DEFINES]->(CodeSymbol)`.
- **Relationship**: `(CodeSymbol)-[:CALLS]->(CodeSymbol)`.

#### 3. `CodeImport` (n8)
- Properties: `id`, `fileId`, `moduleName`, `names`, `lineNumber`, `isFrom`, `isExternal`.
- **Relationship**: `(CodeFile)-[:IMPORTS]->(CodeImport)`.

### Requirements
- Rename all `snake_case` fields (e.g., `lines_of_code`) to `camelCase` (`linesOfCode`) in `entities.py`.
- Update the `parser.py` logic to populate these new property names correctly.
- Ensure `SymbolType` Enum matches the v1.0 documentation.

### Business Value
This alignment is critical for **Impact Analysis**. By having granular, correctly labeled code symbols, the system can accurately predict how a change in one method affects the rest of the architecture.

## Status: COMPLETED
