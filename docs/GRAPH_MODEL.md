# Neo4j Graph Model - SocialSeed Tasker

This document describes the complete graph schema for the SocialSeed Tasker project.

## Version: 0.9.0

## Node Types

### 1. Issue
Represents a task, bug, or feature to be addressed.

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `title` | String | Issue title |
| `description` | String | Detailed description |
| `status` | Enum | OPEN, IN_PROGRESS, BLOCKED, COMPLETED, CLOSED |
| `priority` | Enum | LOW, MEDIUM, HIGH, CRITICAL |
| `component_id` | UUID | Associated component |
| `project` | String | Project name |
| `labels` | List[String] | Issue labels |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update |
| `closed_at` | DateTime | Close timestamp |

### 2. Component
Represents a service/module that groups issues.

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | Component name |
| `project` | String | Project name |
| `description` | String | Component description |
| `created_at` | DateTime | Creation timestamp |

### 3. Agent (v0.9.0)
Represents an AI agent in the system.

| Property | Type | Description |
|----------|------|-------------|
| `id` | String | Agent identifier |
| `name` | String | Agent name |
| `role` | Enum | DEVELOPER, REVIEWER, ARCHITECT, etc. |
| `status` | Enum | IDLE, WORKING, BLOCKED, OFFLINE |
| `capabilities` | List[String] | Agent capabilities |
| `created_at` | DateTime | Creation timestamp |

### 4. CodeFile (v0.9.0)
Represents a source file in the code graph.

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | File name |
| `path` | String | Relative file path |
| `language` | String | Programming language |
| `lines_of_code` | Integer | Number of lines |
| `file_hash` | String | File content hash |
| `repository_path` | String | Repository root path |
| `commit_sha` | String | Git commit |
| `scanned_at` | DateTime | Scan timestamp |

### 5. CodeSymbol (v0.9.0)
Represents a code symbol (function, class, method).

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | Symbol name |
| `symbol_type` | Enum | FUNCTION, CLASS, METHOD, etc. |
| `file_id` | UUID | Parent file |
| `start_line` | Integer | Start line in file |
| `end_line` | Integer | End line in file |
| `start_column` | Integer | Start column |
| `end_column` | Integer | End column |
| `parameters` | List[String] | Function parameters |
| `return_type` | String | Return type |
| `decorators` | List[String] | Decorators |
| `is_test` | Boolean | Is test file |
| `parent_symbol_id` | UUID | Parent symbol (for methods) |

### 6. CodeImport (v0.9.0)
Represents an import statement.

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `file_id` | UUID | Parent file |
| `module` | String | Imported module |
| `names` | List[String] | Specific names imported |
| `line_number` | Integer | Line in file |
| `is_from` | Boolean | Is from import |

### 7. RAGEmbedding (v0.9.0)
Stores embeddings for semantic search.

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `content` | String | Text content |
| `embedding` | List[Float] | Vector embedding (1536 dims) |
| `source_type` | String | Type: issue, adr, code, doc |
| `source_id` | UUID | Source document ID |
| `created_at` | DateTime | Creation timestamp |

### 8. ReasoningNode (v0.9.0)
Records agent reasoning for transparency.

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `thought` | String | Agent's reasoning text |
| `confidence` | Float | Confidence score (0.0-1.0) |
| `alternatives_considered` | List[String] | Options evaluated |
| `rejected_reasons` | List[String] | Why alternatives rejected |
| `decision` | String | Decision made |
| `decision_type` | Enum | solution_selection, architecture_choice, etc. |
| `created_at` | DateTime | When thought occurred |

### 9. Label
Represents issue labels/tags.

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | String | Label name |
| `color` | String | Hex color code |

---

## Relationship Types

### Core Task Management

| From | To | Type | Properties |
|------|-----|------|-------------|
| Issue | Issue | `DEPENDS_ON` | - |
| Issue | Issue | `BLOCKS` | - |
| Issue | Issue | `RELATES_TO` | - |
| Issue | Issue | `CAUSED_BY` | - |
| Issue | Issue | `IS_DUPLICATE_OF` | - |
| Issue | Component | `BELONGS_TO` | - |
| Issue | Issue | `HAS_SUBTASK` | - |
| Issue | Label | `HAS_LABEL` | - |
| Component | Component | `DEPENDS_ON` | - |

### Code-as-Graph (v0.9.0)

| From | To | Type | Properties |
|------|-----|------|-------------|
| CodeFile | CodeSymbol | `DEFINES` | - |
| CodeFile | CodeImport | `IMPORTS` | - |
| CodeSymbol | CodeSymbol | `CALLS` | - |
| CodeSymbol | CodeSymbol | `CONTAINS` | - |
| CodeSymbol | CodeSymbol | `EXTENDS` | - |
| CodeSymbol | CodeSymbol | `IMPLEMENTS` | - |

### AI Reasoning (v0.9.0)

| From | To | Type | Properties |
|------|-----|------|-------------|
| Agent | ReasoningNode | `THOUGHT` | timestamp |
| ReasoningNode | Issue | `DECIDED` | - |
| ReasoningFeedback | ReasoningNode | `FEEDS_BACK` | - |

---

## Schema Constraints

```cypher
CREATE CONSTRAINT issue_id IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE
CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE
CREATE CONSTRAINT code_file_id IF NOT EXISTS FOR (f:CodeFile) REQUIRE f.id IS UNIQUE
CREATE CONSTRAINT code_symbol_id IF NOT EXISTS FOR (s:CodeSymbol) REQUIRE s.id IS UNIQUE
CREATE CONSTRAINT code_import_id IF NOT EXISTS FOR (i:CodeImport) REQUIRE i.id IS UNIQUE
CREATE CONSTRAINT reasoning_id IF NOT EXISTS FOR (r:ReasoningNode) REQUIRE r.id IS UNIQUE
CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE
```

---

## Schema Indexes

### Core
```cypher
CREATE INDEX issue_status IF NOT EXISTS FOR (i:Issue) ON (i.status)
CREATE INDEX issue_component IF NOT EXISTS FOR (i:Issue) ON (i.component_id)
CREATE INDEX issue_priority IF NOT EXISTS FOR (i:Issue) ON (i.priority)
CREATE INDEX issue_created_at IF NOT EXISTS FOR (i:Issue) ON (i.created_at)
CREATE INDEX component_name IF NOT EXISTS FOR (c:Component) ON (c.name)
```

### Code Graph
```cypher
CREATE INDEX code_file_path IF NOT EXISTS FOR (f:CodeFile) ON (f.path)
CREATE INDEX code_file_name IF NOT EXISTS FOR (f:CodeFile) ON (f.name)
CREATE INDEX code_symbol_name IF NOT EXISTS FOR (s:CodeSymbol) ON (s.name)
CREATE INDEX code_symbol_type IF NOT EXISTS FOR (s:CodeSymbol) ON (s.symbol_type)
```

### Reasoning
```cypher
CREATE INDEX reasoning_type IF NOT EXISTS FOR (r:ReasoningNode) ON (r.decision_type)
CREATE INDEX reasoning_created IF NOT EXISTS FOR (r:ReasoningNode) ON (r.created_at)
```

---

## Query Examples

### Get issue with dependencies
```cypher
MATCH (i:Issue {id: $issue_id})
OPTIONAL MATCH (i)-[:DEPENDS_ON]->(dep)
OPTIONAL MATCH (i)<-[:BLOCKS]-(blocked)
RETURN i, collect(dep) as dependencies, collect(blocked) as blockers
```

### Get code file with symbols
```cypher
MATCH (f:CodeFile {id: $file_id})
MATCH (f)<-[:DEFINES]-(s:CodeSymbol)
RETURN f, collect(s) as symbols
```

### Get agent reasoning for issue
```cypher
MATCH (a:Agent)-[:THOUGHT]->(r:ReasoningNode)-[:DECIDED]->(i:Issue {id: $issue_id})
RETURN a.name as agent, r.thought, r.confidence, r.decision
ORDER BY r.created_at DESC
```

### Semantic search with RAG
```cypher
CALL db.index.vector.searchNodes('rag_index', 5, $query_embedding)
YIELD node, score
RETURN node.content, score
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.9.0 | 2026-04-30 | Added Code-as-Graph, RAG, AI Reasoning nodes |
| 0.8.0 | - | Core task management |