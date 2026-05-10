# Skill: Code-as-Graph Analysis for Issue Resolution

## Purpose
This skill enables programming agents to perform impact analysis and causal traceability by leveraging the graph model relationships defined in `GraphDataModelDetails.md`.

## When to Use
This skill is activated when:
- Agent needs to resolve an issue (Phase 4 of TEST workflow)
- Agent needs to understand what code will be affected
- Agent needs to verify no breaking changes are introduced

---

## Graph Relationships for Issue Resolution

### Required Flow for Each Issue

```cypher
# 1. Get Issue Details
GET /api/v1/issues/{issue_id}

# 2. Check Dependencies (must be CLOSED)
GET /api/v1/issues/{issue_id}/dependencies

# 3. Identify Affected Components
GET /api/v1/components?project={project_id}

# 4. Query Affected Code Symbols (if linked)
GET /api/v1/code/symbols?issue_id={issue_id}

# 5. Check Policies for Component
GET /api/v1/policies?component_id={component_id}

# 6. Perform Impact Analysis (before changes)
# Query: What methods call the symbols I'm modifying?
MATCH (s:CodeSymbol)<-[:CALLS*1..3]-(dependent)
WHERE s.id IN {affected_symbols}
RETURN dependent.name, dependent.symbolType
```

---

## Node Relationships Mapping

### Issue Resolution Flow

| Step | Action | Graph Relationship | API Endpoint |
|------|--------|-------------------|---------------|
| 1 | Create Issue | `(Project)-[:HAS_ISSUE]->(Issue)` | `POST /api/v1/issues` |
| 2 | Assign to Component | `(Issue)-[:PART_OF]->(Component)` | `POST /api/v1/issues` (component_id) |
| 3 | Add Dependencies | `(Issue)-[:DEPENDS_ON]->(Issue)` | `POST /api/v1/issues/{id}/dependencies` |
| 4 | Assign to Agent | `(Agent)-[:ASSIGNED_TO]->(Issue)` | `POST /api/v1/issues/{id}/assign` |
| 5 | Create Reasoning | `(Agent)-[:PRODUCED]->(ReasoningNode)` | `POST /api/v1/issues/{id}/reasoning` |
| 6 | Validate (Human) | `(User)-[:VALIDATES]->(ReasoningNode)` | `POST /api/v1/reasoning/{id}/validate` |
| 7 | Implement Code | `(Commit)-[:MODIFIED]->(CodeFile)` | Git commit |
| 8 | Link to Issue | `(Issue)-[:RESOLVED_BY]->(Commit)` | `POST /api/v1/issues/{id}/close` |
| 9 | Check Policies | `(Agent)-[:MUST_COMPLY_WITH]->(Policy)` | `GET /api/v1/policies/validate` |

---

## Mandatory Graph Queries for Agents

### Before Implementation (Pre-Analysis)

```python
# 1. Get component context
component = GET /api/v1/components/{component_id}

# 2. Get project policies
policies = GET /api/v1/policies?project_id={project_id}

# 3. Get existing code structure (if applicable)
code_files = GET /api/v1/code/files?component={component_id}

# 4. Check for linked CodeSymbols
symbols = GET /api/v1/code/symbols?issue={issue_id}
```

### During Implementation

```python
# 5. Before modifying a method, check what calls it
impact_query = """
MATCH (s:CodeSymbol {name: $method_name})<-[:CALLS*1..3]-(dependent)
RETURN dependent.name as affected_method, dependent.symbolType
"""
```

### After Implementation (Post-Analysis)

```python
# 6. Verify no policy violations
violations = GET /api/v1/policies/validate

# 7. Record the commit
commit = POST /api/v1/commits (creates Commit node)

# 8. Link commit to issue (RESOLVED_BY relationship)
issue = POST /api/v1/issues/{id}/close (adds resolution and commit link)
```

---

## CodeSymbol Impact Analysis

When modifying code, agents MUST perform impact analysis:

### Query: Find all methods that call the modified method
```cypher
MATCH (modified:CodeSymbol {name: 'calculateTotal'})<-[:CALLS]-(caller:CodeSymbol)
RETURN caller.name, caller.symbolType
```

### Query: Find all files that import the modified module
```cypher
MATCH (file:CodeFile)-[:IMPORTS]->(imp:CodeImport {moduleName: 'utils'})
RETURN file.path, file.language
```

### Query: Check policy violations for component
```cypher
MATCH (p:Policy {isActive: true})-[:APPLIES_TO]->(c:Component {id: $component_id})
RETURN p.name, p.severity, p.targetScope
```

---

## ReasoningNode Integration

Every implementation MUST create a reasoning trace:

```python
reasoning = {
    "context": "implementation",
    "thought": "Approach and rationale for the solution",
    "confidence": 0.95,
    "decisionType": "FEATURE",  # or BUG_FIX, REFACTOR
    "related_symbols": ["method_name_1", "method_name_2"],
    "files_modified": ["file1.py", "file2.py"],
    "policies_checked": ["POLICY-001", "POLICY-002"],
    "impact_analysis": "List of affected methods"
}
POST /api/v1/issues/{id}/reasoning
```

---

## Policy Compliance Workflow

### Before any code change:
```python
# 1. Fetch relevant policies
policies = GET /api/v1/policies?target_scope={COMPONENT|CODE_SYMBOL|COMMIT}

# 2. Analyze code against policies
violations = POST /api/v1/policies/validate {
    "files": [...],
    "component_id": "..."
}

# 3. If BLOCKER severity violation:
#    - DO NOT proceed
#    - Use remediation_strategy to fix
#    - Re-validate
```

---

## Integration with TEST Workflow (Phase 4)

When executing TEST workflow Phase 4, agents MUST:

1. **Load this skill** alongside `programming-agent-governance.md`
2. **Query the graph** to understand context before implementing
3. **Perform impact analysis** for any code modification
4. **Link CodeSymbols** to issues if applicable
5. **Verify policies** before closing
6. **Create complete reasoning trace** including:
   - What symbols were affected
   - What was the impact analysis result
   - Which policies were checked

---

## Audit Criteria

- **Graph Awareness**: Did the agent query the graph to understand context?
- **Impact Analysis**: Did the agent check what code would be affected?
- **Policy Compliance**: Did the agent validate against policies before changes?
- **Causal Traceability**: Does the reasoning log link to CodeSymbols?
- **Complete Resolution**: Does the issue close include commit hash and reasoning?

---

## Skills Loading Order

For TEST workflow Phase 4, agents MUST load:
1. `.agent/skills/programming-agent-governance.md` (Primary)
2. `.agent/skills/code-as-graph-analysis.md` (For graph queries)
3. `.agent/skills/documentation-sync.md` (For docs)
4. `.agent/skills/hexagonal-architecture.md` (For architecture)