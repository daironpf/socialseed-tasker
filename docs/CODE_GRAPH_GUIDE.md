# Developer Guide: Code-as-Graph (v0.9.0)

This guide covers the Code-as-Graph feature in SocialSeed Tasker v0.9.0.

## Overview

Code-as-Graph uses Tree-sitter to parse source code and create a graph representation in Neo4j, enabling powerful code analysis and impact estimation.

## Features

- **Multi-language support**: Python, JavaScript, TypeScript, Java, C++
- **Symbol extraction**: Functions, classes, methods, variables
- **Import tracking**: Track module dependencies
- **Call graph**: Understand function call relationships
- **Impact analysis**: Estimate blast radius of changes

## Architecture

### Parser (Tree-sitter)
The parser extracts:
- CodeFiles (source files)
- CodeSymbols (functions, classes)
- CodeImports (import statements)

### Graph Model
```
CodeFile --DEFINES--> CodeSymbol --CALLS--> CodeSymbol
CodeFile --IMPORTS--> CodeImport
```

## Usage

### CLI Commands

#### Scan Repository
```bash
tasker code-graph scan /path/to/repo
```

This will:
1. Traverse all source files
2. Parse using Tree-sitter
3. Create nodes and relationships in Neo4j

#### Find Symbols
```bash
# Find function by name
tasker code-graph find --name "calculate_total"

# Find by type
tasker code-graph find --type class --name "UserService"
```

#### List Files
```bash
# All Python files
tasker code-graph files --language python

# All JavaScript files
tasker code-graph files --language javascript
```

#### Graph Statistics
```bash
tasker code-graph stats
```

Output:
```
Code Files: 150
Code Symbols: 1,250
Imports: 890
Functions: 680
Classes: 120
```

#### Impact Analysis
```bash
# Find what would be affected by changing a function
tasker code-graph impact <symbol-id>
```

#### Find Callers
```bash
# Find functions that call a specific function
tasker code-graph calls <symbol-id>
```

#### Find Dependencies
```bash
# Find external dependencies of a function
tasker code-graph depends <symbol-id>
```

#### Find Tests
```bash
# Find tests related to a function
tasker code-graph tests <symbol-id>
```

#### Clear Graph
```bash
tasker code-graph clear
```

### API Endpoints

#### Scan Repository
```bash
POST /api/v1/code-graph/scan
{
  "repository_path": "/path/to/repo"
}
```

#### Find Symbols
```bash
GET /api/v1/code-graph/find?name=function_name&language=python
```

#### Get File Details
```bash
GET /api/v1/code-graph/file?path=src/main.py
```

#### Impact Analysis
```bash
GET /api/v1/code-graph/impact/{symbol_id}
```

## Supported Languages

| Language | Extensions | Status |
|----------|------------|--------|
| Python | .py | ✅ Full |
| JavaScript | .js | ✅ Full |
| TypeScript | .ts, .tsx | ✅ Full |
| Java | .java | ✅ Full |
| C++ | .cpp, .cc, .h | ✅ Full |

## Graph Schema

### Nodes

```cypher
(:CodeFile {
  id: UUID,
  name: String,
  path: String,
  language: String,
  lines_of_code: Integer,
  file_hash: String
})

(:CodeSymbol {
  id: UUID,
  name: String,
  symbol_type: String,  -- FUNCTION, CLASS, METHOD, etc.
  start_line: Integer,
  end_line: Integer,
  parameters: List,
  return_type: String
})

(:CodeImport {
  id: UUID,
  module: String,
  names: List,
  line_number: Integer
})
```

### Relationships

```cypher
// File defines symbols
(f:CodeFile)-[:DEFINES]->(s:CodeSymbol)

// File imports modules
(f:CodeFile)-[:IMPORTS]->(i:CodeImport)

// Symbol calls another symbol
(s1:CodeSymbol)-[:CALLS]->(s2:CodeSymbol)

// Symbol contains nested symbols
(s1:CodeSymbol)-[:CONTAINS]->(s2:CodeSymbol)

// Class extends another class
(c1:CodeSymbol)-[:EXTENDS]->(c2:CodeSymbol)

// Class implements interface
(c:CodeSymbol)-[:IMPLEMENTS]->(i:CodeSymbol)
```

## Constraints and Indexes

```cypher
CREATE CONSTRAINT code_file_id IF NOT EXISTS FOR (f:CodeFile) REQUIRE f.id IS UNIQUE
CREATE CONSTRAINT code_symbol_id IF NOT EXISTS FOR (s:CodeSymbol) REQUIRE s.id IS UNIQUE
CREATE CONSTRAINT code_import_id IF NOT EXISTS FOR (i:CodeImport) REQUIRE i.id IS UNIQUE

CREATE INDEX code_file_path IF NOT EXISTS FOR (f:CodeFile) ON (f.path)
CREATE INDEX code_symbol_name IF NOT EXISTS FOR (s:CodeSymbol) ON (s.name)
CREATE INDEX code_symbol_type IF NOT EXISTS FOR (s:CodeSymbol) ON (s.symbol_type)
```

## Example Queries

### Get all functions in a file
```cypher
MATCH (f:CodeFile {path: 'src/main.py'})
MATCH (f)<-[:DEFINES]-(s:CodeSymbol {symbol_type: 'FUNCTION'})
RETURN s.name, s.start_line, s.end_line
```

### Get call graph for a function
```cypher
MATCH (s:CodeSymbol {name: 'process_payment'})
MATCH path = (s)<-[:CALLS*1..5]-(caller)
RETURN caller.name, length(path) as distance
ORDER BY distance
```

### Find all test files for a module
```bash
tasker code-graph tests <module_symbol_id>
```

Cypher equivalent:
```cypher
MATCH (m:CodeSymbol {name: 'UserService'})
MATCH (t:CodeSymbol)<-[:CALLS]-(test:CodeSymbol)
WHERE t.is_test = true OR test.name CONTAINS 'test'
RETURN test.name, test.path
```

### Impact analysis - what breaks if we change this?
```bash
tasker code-graph impact <symbol_id>
```

Cypher equivalent:
```cypher
MATCH (s:CodeSymbol {id: 'uuid'})
MATCH (s)<-[:CALLS]-(callers)
MATCH (s)<-[:IMPLEMENTS]-(implementers)
RETURN 'callers' as type, collect(caller.name) as affected
UNION
RETURN 'implementers' as type, collect(implementer.name) as affected
```

## Integration with Agents

### Get Context
```bash
tasker agent context --issue <issue-id>
```

This provides the agent with:
1. Relevant code symbols for the issue
2. Call graph context
3. Test coverage information
4. Similar past solutions (via RAG)

## Best Practices

1. **Scan after major changes** - Re-scan after refactoring
2. **Use impact analysis** - Before making changes, check blast radius
3. **Track test relationships** - Know what tests cover your code
4. **Combine with RAG** - Use semantic search + code graph for complete context

## Performance Tips

- Scan during off-peak hours for large repos
- Use language filters to scan incrementally
- Clear and re-scan periodically to keep graph updated

## Troubleshooting

### No symbols found
- Ensure file extensions are supported
- Check Tree-sitter grammars are installed

### Incomplete call graph
- Some dynamic calls may not be detected
- Manual review recommended for critical functions

### Performance issues
- Add more indexes for frequent queries
- Consider incremental scanning instead of full scan